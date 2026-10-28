"""Whisker 自有 x86-64 机器码编码器（不依赖汇编器/编译器/LLVM）

设计取舍：
  - 只覆盖我们代码生成真正用到的指令子集，不求全
  - 所有跳转/调用统一用 rel32（不做短跳优化），标签解析在 resolve() 阶段统一回填
  - 跨段引用（.text 引用 .data/.rdata 里的标签）用 RIP 相对寻址记录成 fixup，
    等 PE 各段 RVA 定下来之后再回填——这样就不需要在汇编期知道段的最终地址
"""
from __future__ import annotations

import struct

# 通用寄存器编号
RAX, RCX, RDX, RBX, RSP, RBP, RSI, RDI = 0, 1, 2, 3, 4, 5, 6, 7
R8, R9, R10, R11, R12, R13, R14, R15 = 8, 9, 10, 11, 12, 13, 14, 15

REG_NAMES = {
    RAX: "rax", RCX: "rcx", RDX: "rdx", RBX: "rbx", RSP: "rsp", RBP: "rbp",
    RSI: "rsi", RDI: "rdi", R8: "r8", R9: "r9", R10: "r10", R11: "r11",
    R12: "r12", R13: "r13", R14: "r14", R15: "r15",
}

# 条件码（jcc / setcc 的低 4 位）
CC = {"o": 0x0, "no": 0x1, "b": 0x2, "ae": 0x3, "e": 0x4, "ne": 0x5,
      "be": 0x6, "a": 0x7, "s": 0x8, "ns": 0x9, "p": 0xA, "np": 0xB,
      "l": 0xC, "ge": 0xD, "le": 0xE, "g": 0xF}


def _modrm(mod: int, reg: int, rm: int) -> int:
    return ((mod & 3) << 6) | ((reg & 7) << 3) | (rm & 7)


def _rex(w: int, r: int, x: int, b: int) -> bytes:
    v = 0x40 | ((w & 1) << 3) | ((r >> 3 & 1) << 2) | ((x >> 3 & 1) << 1) | (b >> 3 & 1)
    return b"" if v == 0x40 else bytes([v])


class Asm:
    """一个小的 x86-64 文本段汇编器"""

    def __init__(self) -> None:
        self.code = bytearray()
        self.labels: dict[str, int] = {}
        self._jmp_fixups: list[tuple[int, str]] = []       # (disp32 字段偏移, 标签)
        self._text_rip_fixups: list[tuple[int, int, str]] = []   # 段内 RIP 相对代码引用
        self.rip_fixups: list[tuple[int, int, str]] = []   # (disp32 字段偏移, 指令结束偏移, 数据标签)
        self.listing: list[tuple[int, str]] = []           # 便于 --dump-asm 自检

    # ---------- 基础 ----------
    def emit(self, *parts: int | bytes) -> None:
        for p in parts:
            if isinstance(p, int):
                self.code.append(p & 0xFF)
            else:
                self.code.extend(p)

    @property
    def here(self) -> int:
        return len(self.code)

    def label(self, name: str) -> None:
        assert name not in self.labels, f"标签重复：{name}"
        self.labels[name] = self.here

    def note(self, text: str) -> None:
        self.listing.append((self.here, text))

    # ---------- MOV ----------
    def mov_rr(self, dst: int, src: int) -> None:
        self.emit(_rex(1, src, 0, dst), 0x89, _modrm(3, src, dst))

    def mov_ri(self, reg: int, imm: int) -> None:
        if -0x80000000 <= imm <= 0x7FFFFFFF:
            self.emit(_rex(1, 0, 0, reg), 0xC7, _modrm(3, 0, reg), struct.pack("<i", imm))
        else:
            # 按 64 位位模式写出（立即数可能是无符号大数，如除法魔数）
            self.emit(_rex(1, 0, 0, reg), 0xB8 + (reg & 7),
                      struct.pack("<Q", imm & 0xFFFFFFFFFFFFFFFF))

    def _mem_parts(self, reg: int, base: int, disp: int) -> tuple[bytes, bytes]:
        """返回 (REX 前缀, modrm+sib+disp)。REX 必须在 opcode 之前，其余在之后。"""
        need_sib = (base & 7) == 4          # rsp / r12 必须走 SIB
        if need_sib:
            sib = bytes([_modrm(0, 4, base & 7)])   # scale=0, index=none, base
            if disp == 0:
                return _rex(1, reg, 0, base), bytes([_modrm(0, reg, 4)]) + sib
            if -128 <= disp <= 127:
                return _rex(1, reg, 0, base), bytes([_modrm(1, reg, 4)]) + sib + bytes([disp & 0xFF])
            return _rex(1, reg, 0, base), bytes([_modrm(2, reg, 4)]) + sib + struct.pack("<i", disp)
        if base == RBP and disp == 0:
            return _rex(1, reg, 0, base), bytes([_modrm(1, reg, base), 0])
        if -128 <= disp <= 127:
            return _rex(1, reg, 0, base), bytes([_modrm(1, reg, base), disp & 0xFF])
        return _rex(1, reg, 0, base), bytes([_modrm(2, reg, base)]) + struct.pack("<i", disp)

    def mov_rm(self, reg: int, base: int, disp: int = 0) -> None:
        """reg <- [base+disp]"""
        rex, tail = self._mem_parts(reg, base, disp)
        self.emit(rex, 0x8B, tail)

    def mov_mr(self, base: int, disp: int, reg: int) -> None:
        """[base+disp] <- reg"""
        rex, tail = self._mem_parts(reg, base, disp)
        self.emit(rex, 0x89, tail)

    def mov_mi(self, base: int, disp: int, imm: int) -> None:
        """[base+disp] <- imm32（符号扩展为 64 位）"""
        rex, tail = self._mem_parts(0, base, disp)
        self.emit(rex, 0xC7, tail, struct.pack("<i", imm))

    def _mem8_parts(self, reg: int, base: int, disp: int) -> tuple[bytes, bytes]:
        need_sib = (base & 7) == 4
        if need_sib:
            sib = bytes([_modrm(0, 4, base & 7)])
            if disp == 0:
                return _rex(0, reg, 0, base), bytes([_modrm(0, reg, 4)]) + sib
            if -128 <= disp <= 127:
                return _rex(0, reg, 0, base), bytes([_modrm(1, reg, 4)]) + sib + bytes([disp & 0xFF])
            return _rex(0, reg, 0, base), bytes([_modrm(2, reg, 4)]) + sib + struct.pack("<i", disp)
        if -128 <= disp <= 127:
            return _rex(0, reg, 0, base), bytes([_modrm(1, reg, base), disp & 0xFF])
        return _rex(0, reg, 0, base), bytes([_modrm(2, reg, base)]) + struct.pack("<i", disp)

    def mov_mr8(self, base: int, disp: int, reg: int) -> None:
        """[base+disp] <- reg 的低字节"""
        rex, tail = self._mem8_parts(reg, base, disp)
        self.emit(rex, 0x88, tail)

    def mov_rm8(self, reg: int, base: int, disp: int = 0) -> None:
        """reg 的低字节 <- [base+disp]"""
        rex, tail = self._mem8_parts(reg, base, disp)
        self.emit(rex, 0x8A, tail)

    # ---------- RIP 相对数据访问 ----------
    def _rip_ref(self, opcode: int, reg: int, target_label: str) -> None:
        self.emit(_rex(1, reg, 0, 0), opcode, _modrm(0, reg, 5))
        disp_off = self.here
        self.emit(struct.pack("<i", 0))
        self.rip_fixups.append((disp_off, self.here, target_label))

    def mov_r_rip(self, reg: int, target_label: str) -> None:
        """reg <- [rip+label]（加载全局变量）"""
        self._rip_ref(0x8B, reg, target_label)

    def mov_rip_r(self, target_label: str, reg: int) -> None:
        """[rip+label] <- reg（写全局变量）"""
        self._rip_ref(0x89, reg, target_label)

    def lea_rip(self, reg: int, target_label: str) -> None:
        """reg <- rip+label（取数据地址）"""
        self._rip_ref(0x8D, reg, target_label)

    def lea_rip_code(self, reg: int, target_label: str) -> None:
        """reg <- rip+label（取段内代码地址，用于函数指针）"""
        self.emit(_rex(1, reg, 0, 0), 0x8D, _modrm(0, reg, 5))
        off = self.here
        self.emit(struct.pack("<i", 0))
        self._text_rip_fixups.append((off, self.here, target_label))

    def call_rip(self, target_label: str) -> None:
        """间接调用 [rip+label]（调导入函数：loader 回填 IAT 后即为真实地址）"""
        self.emit(_rex(0, 0, 0, 0), 0xFF, _modrm(0, 2, 5))
        disp_off = self.here
        self.emit(struct.pack("<i", 0))
        self.rip_fixups.append((disp_off, self.here, target_label))

    # ---------- 算术/逻辑 ----------
    def _binop(self, opcode: int, dst: int, src: int) -> None:
        self.emit(_rex(1, src, 0, dst), opcode, _modrm(3, src, dst))

    def add_rr(self, dst: int, src: int) -> None: self._binop(0x01, dst, src)
    def sub_rr(self, dst: int, src: int) -> None: self._binop(0x29, dst, src)
    def and_rr(self, dst: int, src: int) -> None: self._binop(0x21, dst, src)
    def or_rr(self, dst: int, src: int) -> None: self._binop(0x09, dst, src)
    def xor_rr(self, dst: int, src: int) -> None: self._binop(0x31, dst, src)

    # 内存操作数形式：dst op= [base+disp]（用于把局部变量/字段直接当操作数）
    def _binop_rm(self, opcode: int, dst: int, base: int, disp: int) -> None:
        rex, tail = self._mem_parts(dst, base, disp)
        self.emit(rex, opcode, tail)

    def add_rm(self, dst: int, base: int, disp: int = 0) -> None: self._binop_rm(0x03, dst, base, disp)
    def sub_rm(self, dst: int, base: int, disp: int = 0) -> None: self._binop_rm(0x2B, dst, base, disp)
    def and_rm(self, dst: int, base: int, disp: int = 0) -> None: self._binop_rm(0x23, dst, base, disp)
    def or_rm(self, dst: int, base: int, disp: int = 0) -> None: self._binop_rm(0x0B, dst, base, disp)
    def cmp_rm(self, a: int, base: int, disp: int = 0) -> None: self._binop_rm(0x3B, a, base, disp)

    def lea_mem(self, reg: int, base: int, disp: int = 0) -> None:
        """lea reg, [base+disp]"""
        rex, tail = self._mem_parts(reg, base, disp)
        self.emit(rex, 0x8D, tail)

    # ---------- 带下标的寻址：[base + index*scale + disp] ----------
    def _sib_parts(self, reg: int, base: int, index: int, scale: int, disp: int,
                   w: int = 1) -> tuple[bytes, bytes]:
        assert (index & 7) != 4, "不能用 rsp 当下标寄存器（SIB 里 100 表示无下标）"
        scale_bits = {1: 0, 2: 1, 4: 2, 8: 3}[scale]
        sib = bytes([(scale_bits << 6) | ((index & 7) << 3) | (base & 7)])
        rex = _rex(w, reg, index, base)
        if disp == 0 and (base & 7) != 5:
            return rex, bytes([_modrm(0, reg, 4)]) + sib
        if -128 <= disp <= 127:
            return rex, bytes([_modrm(1, reg, 4)]) + sib + bytes([disp & 0xFF])
        return rex, bytes([_modrm(2, reg, 4)]) + sib + struct.pack("<i", disp)

    def mov_rm_sib(self, dst: int, base: int, index: int, scale: int = 8, disp: int = 0) -> None:
        """dst <- [base + index*scale + disp]"""
        rex, tail = self._sib_parts(dst, base, index, scale, disp)
        self.emit(rex, 0x8B, tail)

    def mov_mr_sib(self, base: int, index: int, src: int, scale: int = 8, disp: int = 0) -> None:
        """[base + index*scale + disp] <- src"""
        rex, tail = self._sib_parts(src, base, index, scale, disp)
        self.emit(rex, 0x89, tail)

    def lea_mem_sib(self, dst: int, base: int, index: int, scale: int = 8, disp: int = 0) -> None:
        """dst <- base + index*scale + disp（取地址）"""
        rex, tail = self._sib_parts(dst, base, index, scale, disp)
        self.emit(rex, 0x8D, tail)
    def cmp_rr(self, a: int, b: int) -> None: self._binop(0x39, a, b)   # 比较 a - b
    def test_rr(self, a: int, b: int) -> None: self._binop(0x85, a, b)

    def cmp_ri(self, reg: int, imm: int) -> None:
        if -128 <= imm <= 127:
            self.emit(_rex(1, 0, 0, reg), 0x83, _modrm(3, 7, reg), imm & 0xFF)
        else:
            self.emit(_rex(1, 0, 0, reg), 0x81, _modrm(3, 7, reg), struct.pack("<i", imm))

    def add_ri(self, reg: int, imm: int) -> None:
        if -128 <= imm <= 127:
            self.emit(_rex(1, 0, 0, reg), 0x83, _modrm(3, 0, reg), imm & 0xFF)
        else:
            self.emit(_rex(1, 0, 0, reg), 0x81, _modrm(3, 0, reg), struct.pack("<i", imm))

    def sub_ri(self, reg: int, imm: int) -> None:
        if -128 <= imm <= 127:
            self.emit(_rex(1, 0, 0, reg), 0x83, _modrm(3, 5, reg), imm & 0xFF)
        else:
            self.emit(_rex(1, 0, 0, reg), 0x81, _modrm(3, 5, reg), struct.pack("<i", imm))

    def and_ri(self, reg: int, imm: int) -> None:
        if -128 <= imm <= 127:
            self.emit(_rex(1, 0, 0, reg), 0x83, _modrm(3, 4, reg), imm & 0xFF)
        else:
            self.emit(_rex(1, 0, 0, reg), 0x81, _modrm(3, 4, reg), struct.pack("<i", imm))

    def imul_rr(self, dst: int, src: int) -> None:
        self.emit(_rex(1, dst, 0, src), 0x0F, 0xAF, _modrm(3, dst, src))

    def imul_rm(self, dst: int, base: int, disp: int = 0) -> None:
        rex, tail = self._mem_parts(dst, base, disp)
        self.emit(rex, 0x0F, 0xAF, tail)

    def imul_ri(self, dst: int, imm: int) -> None:
        """imul dst, dst, imm32"""
        self.emit(_rex(1, dst, 0, dst), 0x69, _modrm(3, dst, dst), struct.pack("<i", imm))

    def cqo(self) -> None:
        self.emit(0x48, 0x99)

    def idiv_r(self, reg: int) -> None:
        """有符号除法：rdx:rax / reg → rax 商, rdx 余数（调用前需 cqo）"""
        self.emit(_rex(1, 0, 0, reg), 0xF7, _modrm(3, 7, reg))

    def div_r(self, reg: int) -> None:
        self.emit(_rex(1, 0, 0, reg), 0xF7, _modrm(3, 6, reg))

    def neg_r(self, reg: int) -> None:
        self.emit(_rex(1, 0, 0, reg), 0xF7, _modrm(3, 3, reg))

    def inc_r(self, reg: int) -> None:
        self.emit(_rex(1, 0, 0, reg), 0xFF, _modrm(3, 0, reg))

    def dec_r(self, reg: int) -> None:
        self.emit(_rex(1, 0, 0, reg), 0xFF, _modrm(3, 1, reg))

    def shl_ri(self, reg: int, imm: int) -> None:
        self.emit(_rex(1, 0, 0, reg), 0xC1, _modrm(3, 4, reg), imm & 0xFF)

    def sar_ri(self, reg: int, imm: int) -> None:
        self.emit(_rex(1, 0, 0, reg), 0xC1, _modrm(3, 7, reg), imm & 0xFF)

    def shr_ri(self, reg: int, imm: int) -> None:
        """逻辑右移（无符号）"""
        self.emit(_rex(1, 0, 0, reg), 0xC1, _modrm(3, 5, reg), imm & 0xFF)

    def mul_r(self, reg: int) -> None:
        """无符号乘法 rax * reg → rdx:rax"""
        self.emit(_rex(1, 0, 0, reg), 0xF7, _modrm(3, 4, reg))

    # ---------- 栈 ----------
    def push_r(self, reg: int) -> None:
        self.emit(_rex(0, 0, 0, reg), 0x50 + (reg & 7))

    def pop_r(self, reg: int) -> None:
        self.emit(_rex(0, 0, 0, reg), 0x58 + (reg & 7))

    # ---------- 位/字节 ----------
    def setcc_al(self, cond: str) -> None:
        self.emit(0x0F, 0x90 + CC[cond], 0xC0)

    def movzx_eax_al(self) -> None:
        self.emit(0x0F, 0xB6, 0xC0)

    def movzx_r_from_mem8(self, reg: int, base: int, disp: int = 0) -> None:
        rex, tail = self._mem_parts(reg, base, disp)
        self.emit(rex, 0x0F, 0xB6, tail)

    def rep_movsb(self) -> None:
        self.emit(0xF3, 0xA4)

    # ---------- 原子 / 自旋 ----------
    def xchg_mr(self, base: int, disp: int, reg: int) -> None:
        """xchg [base+disp], reg —— 带内存操作数的 xchg 隐含 LOCK，天然原子"""
        rex, tail = self._mem_parts(reg, base, disp)
        self.emit(rex, 0x87, tail)

    def pause(self) -> None:
        self.emit(0xF3, 0x90)

    # ---------- 控制流 ----------
    def ret(self) -> None:
        self.emit(0xC3)

    def jmp(self, target: str) -> None:
        self.emit(0xE9)
        off = self.here
        self.emit(struct.pack("<i", 0))
        self._jmp_fixups.append((off, target))

    def jcc(self, cond: str, target: str) -> None:
        self.emit(0x0F, 0x80 + CC[cond])
        off = self.here
        self.emit(struct.pack("<i", 0))
        self._jmp_fixups.append((off, target))

    def call(self, target: str) -> None:
        self.emit(0xE8)
        off = self.here
        self.emit(struct.pack("<i", 0))
        self._jmp_fixups.append((off, target))

    def call_r(self, reg: int) -> None:
        self.emit(_rex(0, 0, 0, reg), 0xFF, _modrm(3, 2, reg))

    def call_mem(self, base: int, disp: int) -> None:
        rex, tail = self._mem_parts(2, base, disp)
        self.emit(rex, 0xFF, tail)

    def nop(self) -> None:
        self.emit(0x90)

    # ---------- 栈帧（尺寸事后回填） ----------
    def sub_rsp_placeholder(self) -> int:
        """sub rsp, imm32；返回 imm32 字段偏移，便于之后回填实际帧大小"""
        self.emit(_rex(1, 0, 0, RSP), 0x81, _modrm(3, 5, RSP))
        off = self.here
        self.emit(struct.pack("<i", 0))
        return off

    def patch_i32(self, off: int, value: int) -> None:
        struct.pack_into("<i", self.code, off, value)

    # ---------- 解析 ----------
    def resolve(self) -> bytes:
        """回填段内跳转/调用（rel32）与段内 RIP 相对引用"""
        for off, target in self._jmp_fixups:
            if target not in self.labels:
                raise AssertionError(f"未定义标签：{target}")
            rel = self.labels[target] - (off + 4)
            struct.pack_into("<i", self.code, off, rel)
        self._jmp_fixups.clear()
        for disp_off, instr_end, target in self._text_rip_fixups:
            if target not in self.labels:
                raise AssertionError(f"未定义代码标签：{target}")
            rel = self.labels[target] - instr_end
            struct.pack_into("<i", self.code, disp_off, rel)
        self._text_rip_fixups.clear()
        return bytes(self.code)

    def patch_rip(self, text_rva: int, data_rvas: dict[str, tuple[int, int]]) -> None:
        """回填跨段 RIP 相对引用。data_rvas: label -> (段 RVA, 段内偏移)"""
        for disp_off, instr_end, label in self.rip_fixups:
            if label not in data_rvas:
                raise AssertionError(f"未定义数据标签：{label}")
            sec_rva, sec_off = data_rvas[label]
            target_va = sec_rva + sec_off
            here_va = text_rva + instr_end
            disp = target_va - here_va
            if not (-0x80000000 <= disp <= 0x7FFFFFFF):
                raise AssertionError(f"RIP 相对位移越界：{label}")
            struct.pack_into("<i", self.code, disp_off, disp)