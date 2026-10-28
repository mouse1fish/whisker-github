"""自举第 9 步·准备：把 Whisker 运行时（机器码 + 数据 + 符号）提取成 .wk 常量文件

产物 tools/runtime_blob.wk：
  - rtCode / rtRdata / rtData 三个 i64 数组（每元素打包 8 字节，小端）
  - 一组常量：段布局、符号偏移（rt_init / rt_print_begin / ...）、IAT 位置、导入函数个数
约定（Whisker 侧 pegen.wk 必须用同一套布局）：
  text RVA = 0x1000；rdata RVA 紧随 text（按 0x1000 对齐）；data RVA 紧随 rdata
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from whiskerc.asm_x64 import Asm                    # noqa: E402
from whiskerc.pe_x64 import PEBuilder               # noqa: E402
from whiskerc.runtime_x64 import emit_runtime       # noqa: E402


def align(n: int, a: int) -> int:
    return (n + a - 1) // a * a


def pack(data: bytes) -> list[int]:
    """字节流 → i64 列表（8 字节一组，小端，末尾补零）"""
    out = []
    pad = (-len(data)) % 8
    data = data + b"\x00" * pad
    for i in range(0, len(data), 8):
        out.append(int.from_bytes(data[i:i + 8], "little"))
    return out


def render_array(name: str, vals: list[int], per_line: int = 8) -> str:
    lines = [f"    {name}[{len(vals)}]"]
    for i in range(0, len(vals), per_line):
        chunk = ", ".join(str(v) for v in vals[i:i + per_line])
        lines.append("        " + chunk + ",")
    lines[-1] = lines[-1].rstrip(",")
    lines.append("")
    return "\n".join(lines)


def main() -> int:
    a = Asm()
    pe = PEBuilder()
    emit_runtime(a, pe)
    pe._build_import_items()               # 生成 IAT/ILT/描述符数据项

    text_len = len(a.code)
    TEXT_RVA = 0x1000
    # 固定布局：给用户代码预留 0x10000 字节的 .text 空间，段 RVA 全部固定，
    # 这样 blob 的 RIP 引用永远有效，与用户代码大小无关
    RDATA_RVA = 0x11000
    DATA_RVA = 0x21000
    rdata_rva = RDATA_RVA
    data_rva = DATA_RVA
    image_size = 0x31000
    rdata_size, rdata_off = pe._layout(pe.rdata)
    data_size, data_off = pe._layout(pe.data)

    labels: dict[str, tuple[int, int]] = {}
    for it in pe.rdata:
        labels[it.label] = (rdata_rva, rdata_off[it.label])
        for so, sl in it.sublabels:
            labels[sl] = (rdata_rva, rdata_off[it.label] + so)
    for it in pe.data:
        labels[it.label] = (data_rva, data_off[it.label])
        for so, sl in it.sublabels:
            labels[sl] = (data_rva, data_off[it.label] + so)

    # 回填 blob 自己的跨段引用，得到最终机器码
    a.patch_rip(TEXT_RVA, labels)
    code = a.resolve()

    def raw(items, offs) -> bytes:
        buf = bytearray()
        for it in items:
            want = offs[it.label]
            if len(buf) < want:
                buf.extend(b"\x00" * (want - len(buf)))
            buf.extend(it.data)
        return bytes(buf)

    rdata_bytes = raw(pe.rdata, rdata_off)
    data_bytes = raw(pe.data, data_off)

    # 需要暴露给用户代码的符号（.text 偏移）——导出所有 rt_* 函数
    syms = {}
    for name, off in sorted(a.labels.items()):
        if name.startswith("rt_"):
            syms[name] = off

    iat_rva = data_rva + data_off["__iat__"]
    imports = pe.imports

    # 生成 .wk
    out = []
    out.append("# 运行时机器码 blob（由 tools/extract_runtime.py 生成，勿手改）")
    out.append("# 约定：.text 从 RVA 0x1000 开始，blob 占据开头；用户代码接在其后（16 对齐）")
    out.append("actor RuntimeBlob {")
    out.append(f"    RT_TEXT_LEN: Int = {len(code)}")
    out.append(f"    RT_RDATA_LEN: Int = {len(rdata_bytes)}")
    out.append(f"    RT_DATA_LEN: Int = {len(data_bytes)}")
    out.append(f"    RDATA_RVA: Int = {rdata_rva}")
    out.append(f"    DATA_RVA: Int = {data_rva}")
    out.append(f"    IMAGE_SIZE: Int = {image_size}")
    out.append(f"    IAT_RVA: Int = {iat_rva}")
    out.append(f"    NIMPORT: Int = {len(imports)}")
    for name, off in syms.items():
        out.append(f"    OFF_{name}: Int = {off}")
    out.append("")
    out.append(render_array("rtCode", pack(code)))
    out.append(render_array("rtRdata", pack(rdata_bytes)))
    out.append(render_array("rtData", pack(data_bytes)))
    out.append("}")
    (ROOT / "tools" / "runtime_blob.wk").write_text("\n".join(out), encoding="utf-8")

    print(f"文本段 {len(code)} 字节 | rdata {len(rdata_bytes)} | data {len(data_bytes)}")
    print(f"RVA：text 0x{TEXT_RVA:X} rdata 0x{rdata_rva:X} data 0x{data_rva:X} image 0x{image_size:X}")
    print(f"导入函数 {len(imports)} 个：{', '.join(imports)}")
    print("符号：", {k: hex(v) for k, v in syms.items()})
    print("已生成 tools/runtime_blob.wk")

    blob = code + rdata_bytes + data_bytes
    (ROOT / "build" / "rt_blob.bin").write_bytes(blob)
    print(f"已生成 build/rt_blob.bin（{len(blob)} 字节 = text {len(code)} + rdata {len(rdata_bytes)} + data {len(data_bytes)}）")
    print(f"__iat__ 在 data 内偏移：{data_off['__iat__']}（IAT RVA = 0x{iat_rva:X}）")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())