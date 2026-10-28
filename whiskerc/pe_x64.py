"""Whisker 自有 PE32+ 可执行文件写出器（不依赖链接器/编译器/LLVM）

把「机器码文本段 + 只读数据段 + 可写数据段」拼成 Windows 能直接加载运行的 exe：
  - DOS stub + COFF 头 + PE32+ 可选头 + 段表
  - 导入表（ILT / IAT / hint-name / 描述符），让生成的代码能直接调 kernel32 导出函数
  - 关闭 ASLR（DllCharacteristics = 0），因此不需要重定位表

流程：登记数据项 → 导入函数可多次声明（构建时统一成一张表）→ 布局拿相对偏移 →
算出各段 RVA → 回填代码里的 RIP 相对引用与导入表 → 取最终机器码 → 拼文件
"""
from __future__ import annotations

import struct

SECTION_ALIGN = 0x1000
FILE_ALIGN = 0x200
IMAGE_BASE = 0x140000000
FILE_HEADER_SIZE = 0x40 + 4 + 20 + 240
NUM_SECTIONS = 3


def _align(n: int, a: int) -> int:
    return (n + a - 1) // a * a


class _Item:
    __slots__ = ("label", "data", "align", "sublabels")

    def __init__(self, label: str, data: bytes, align: int) -> None:
        self.label = label
        self.data = bytearray(data)
        self.align = align
        self.sublabels: list[tuple[int, str]] = []


class PEBuilder:
    def __init__(self, dll: str = "kernel32.dll") -> None:
        self.dll = dll
        self.rdata: list[_Item] = []
        self.data: list[_Item] = []
        self.imports: list[str] = []

    # ---------- 数据项登记 ----------
    def rdata_item(self, label: str, data: bytes, align: int = 1) -> _Item:
        it = _Item(label, data, align)
        self.rdata.append(it)
        return it

    def data_item(self, label: str, data: bytes, align: int = 8) -> _Item:
        it = _Item(label, data, align)
        self.data.append(it)
        return it

    def declare_imports(self, funcs: list[str]) -> None:
        """声明需要导入的函数；可多次调用，构建时合并成一张导入表。
        每个函数会在 .data 里得到一个 imp_<名字> 的 8 字节槽位标签。"""
        for f in funcs:
            if f not in self.imports:
                self.imports.append(f)

    # ---------- 布局 ----------
    @staticmethod
    def _layout(items: list[_Item]) -> tuple[int, dict[str, int]]:
        off = 0
        table: dict[str, int] = {}
        for it in items:
            off = _align(off, it.align)
            table[it.label] = off
            for so, sl in it.sublabels:
                table[sl] = off + so
            off += len(it.data)
        return off, table

    def _build_import_items(self) -> None:
        """按最终函数清单生成 IAT / ILT / 描述符 / hint-name / dll 名（只做一次）"""
        if not self.imports or any(it.label == "__iat__" for it in self.data):
            return
        n = len(self.imports)
        iat = self.data_item("__iat__", b"\x00" * (8 * (n + 1)), 8)
        for i, f in enumerate(self.imports):
            iat.sublabels.append((8 * i, "imp_" + f))
        self.rdata_item("__ilt__", b"\x00" * (8 * (n + 1)), 8)
        self.rdata_item("__dllname__", self.dll.encode() + b"\x00", 2)
        self.rdata_item("__idesc__", b"\x00" * (20 * 2), 8)
        for f in self.imports:
            self.rdata_item("hint_" + f, struct.pack("<H", 0) + f.encode() + b"\x00", 2)

    def build(self, asm, entry_offset: int) -> bytes:
        """asm: Asm 实例；先按段布局回填跨段引用，再取最终机器码"""
        self._build_import_items()
        rdata_size, rdata_off = self._layout(self.rdata)
        data_size, data_off = self._layout(self.data)

        def _raw_vsize(payload: int) -> int:
            """段在文件里对齐后的大小；段不能为空，否则加载器直接判镜像无效"""
            return _align(payload, FILE_ALIGN) if payload else FILE_ALIGN

        text_vsize = _raw_vsize(len(asm.code))
        rdata_vsize = _raw_vsize(rdata_size)
        data_vsize = _raw_vsize(data_size)

        # 段 RVA 按「文件对齐后的大小」排布；SizeOfImage 必须覆盖到最后一个段
        text_rva = SECTION_ALIGN
        rdata_rva = text_rva + _align(text_vsize, SECTION_ALIGN)
        data_rva = rdata_rva + _align(rdata_vsize, SECTION_ALIGN)
        size_of_image = _align(data_rva + data_vsize, SECTION_ALIGN)

        labels: dict[str, tuple[int, int]] = {}
        for k, v in rdata_off.items():
            labels[k] = (rdata_rva, v)
        for k, v in data_off.items():
            labels[k] = (data_rva, v)

        # 代码里对数据的 RIP 相对引用（必须在 resolve 之前回填）
        asm.patch_rip(text_rva, labels)
        code = asm.resolve()

        # 导入表内容
        if self.imports:
            n = len(self.imports)
            iat_item = next(it for it in self.data if it.label == "__iat__")
            ilt_item = next(it for it in self.rdata if it.label == "__ilt__")
            idesc_item = next(it for it in self.rdata if it.label == "__idesc__")
            ilt_rva = rdata_rva + rdata_off["__ilt__"]
            iat_rva = data_rva + data_off["__iat__"]
            for i, f in enumerate(self.imports):
                entry = rdata_rva + rdata_off["hint_" + f]
                struct.pack_into("<Q", ilt_item.data, 8 * i, entry)
                struct.pack_into("<Q", iat_item.data, 8 * i, entry)
            struct.pack_into("<IIIII", idesc_item.data, 0,
                             ilt_rva, 0, 0, rdata_rva + rdata_off["__dllname__"], iat_rva)
            import_dir = (rdata_rva + rdata_off["__idesc__"], 20 * 2)
            iat_dir = (iat_rva, 8 * (n + 1))
        else:
            import_dir = (0, 0)
            iat_dir = (0, 0)

        # 段原始数据
        def raw(items: list[_Item], offs: dict[str, int]) -> bytes:
            buf = bytearray()
            for it in items:
                want = offs[it.label]
                if len(buf) < want:
                    buf.extend(b"\x00" * (want - len(buf)))
                buf.extend(it.data)
            return bytes(buf)

        text_raw = code + b"\x00" * (text_vsize - len(code))
        rdata_raw_full = raw(self.rdata, rdata_off)
        data_raw_full = raw(self.data, data_off)
        rdata_raw = rdata_raw_full + b"\x00" * (rdata_vsize - len(rdata_raw_full))
        data_raw = data_raw_full + b"\x00" * (data_vsize - len(data_raw_full))

        headers_size = _align(FILE_HEADER_SIZE + NUM_SECTIONS * 40, FILE_ALIGN)
        ptr_text = headers_size
        ptr_rdata = ptr_text + len(text_raw)
        ptr_data = ptr_rdata + len(rdata_raw)

        # DOS + PE 签名 + COFF + 可选头
        dos = bytearray(0x40)
        dos[0:2] = b"MZ"
        struct.pack_into("<I", dos, 0x3C, 0x40)

        coff = struct.pack("<HHIIIHH", 0x8664, NUM_SECTIONS, 0, 0, 0, 240, 0x0022)

        opt = bytearray(240)
        struct.pack_into("<HBBIIIIIQIIHHHHHHIIIIHHQQQQII", opt, 0,
                         0x20B, 14, 0,
                         len(text_raw), len(rdata_raw) + len(data_raw), 0,
                         text_rva + entry_offset, text_rva,      # PE32+ 没有 BaseOfData
                         IMAGE_BASE, SECTION_ALIGN, FILE_ALIGN,
                         6, 0, 0, 0, 6, 0,
                         0, size_of_image, headers_size, 0,
                         3, 0,
                         0x100000, 0x1000, 0x100000, 0x1000,
                         0, 16)
        struct.pack_into("<II", opt, 112 + 8 * 1, *import_dir)
        struct.pack_into("<II", opt, 112 + 8 * 12, *iat_dir)

        def section(name: str, vsize: int, va: int, raw_data: bytes, ptr: int, chars: int) -> bytes:
            return struct.pack("<8sIIIIIIHHI", name.encode().ljust(8, b"\x00"),
                               vsize, va, len(raw_data), ptr, 0, 0, 0, 0, chars)

        out = bytearray()
        out.extend(dos)
        out.extend(b"PE\x00\x00")
        out.extend(coff)
        out.extend(opt)
        out.extend(section(".text", len(text_raw), text_rva, text_raw, ptr_text, 0x60000020))
        out.extend(section(".rdata", len(rdata_raw), rdata_rva, rdata_raw, ptr_rdata, 0x40000040))
        out.extend(section(".data", len(data_raw), data_rva, data_raw, ptr_data, 0xC0000040))
        out.extend(b"\x00" * (headers_size - len(out)))
        out.extend(text_raw)
        out.extend(rdata_raw)
        out.extend(data_raw)
        return bytes(out)