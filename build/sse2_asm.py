p = r"whiskerc/asm_x64.py"
s = open(p, encoding="utf-8").read()
# 在 movsxd_rax_eax 后面追加 SSE2 方法群
anchor = '''    def movsxd_rax_eax(self) -> None:'''
assert anchor in s
# 找到 movsxd 的完整方法体
idx = s.index(anchor)
end = s.index("\n\n", idx)
# 在它后面追加 SSE2 方法
sse2 = '''
    # ---- SSE2 浮点原语（双精度标量）----

    def _sse2_rr(self, prefix: int, opc: int, dst: int, src: int) -> None:
        """SSE2 寄存器-寄存器操作：prefix + opc + modrm(11 dst src)"""
        rex = 0x00
        if dst >= 8: rex |= 4              # REX.R
        if src >= 8: rex |= 1              # REX.B
        modrm = 0xC0 | ((dst & 7) << 3) | (src & 7)
        if rex: self.emit(rex)
        self.emit(prefix, 0x0F, opc, modrm)

    def movq_xmm_r64(self, xmm: int, r64: int) -> None:
        """movq xmm, r64（F2 REX.W 0F 6E /r）"""
        rex = 0x48                          # REX.W
        if xmm >= 8: rex |= 4              # REX.R
        if r64 >= 8: rex |= 1              # REX.B
        modrm = 0xC0 | ((xmm & 7) << 3) | (r64 & 7)
        self.emit(0xF2, rex, 0x0F, 0x6E, modrm)

    def movq_r64_xmm(self, r64: int, xmm: int) -> None:
        """movq r64, xmm（66 REX.W 0F 7E /r）"""
        rex = 0x48
        if xmm >= 8: rex |= 4
        if r64 >= 8: rex |= 1
        modrm = 0xC0 | ((r64 & 7) << 3) | (xmm & 7)
        self.emit(0x66, rex, 0x0F, 0x7E, modrm)

    def addsd(self, dst: int, src: int) -> None:
        self._sse2_rr(0xF2, 0x58, dst, src)

    def subsd(self, dst: int, src: int) -> None:
        self._sse2_rr(0xF2, 0x5C, dst, src)

    def mulsd(self, dst: int, src: int) -> None:
        self._sse2_rr(0xF2, 0x59, dst, src)

    def divsd(self, dst: int, src: int) -> None:
        self._sse2_rr(0xF2, 0x5E, dst, src)

    def sqrtsd(self, dst: int, src: int) -> None:
        self._sse2_rr(0xF2, 0x51, dst, src)

    def cvtsi2sd(self, xmm: int, r64: int) -> None:
        """cvtsi2sd xmm, r64（F2 REX.W 0F 2A /r）"""
        rex = 0x48
        if xmm >= 8: rex |= 4
        if r64 >= 8: rex |= 1
        modrm = 0xC0 | ((xmm & 7) << 3) | (r64 & 7)
        self.emit(0xF2, rex, 0x0F, 0x2A, modrm)

    def cvttsd2si(self, r64: int, xmm: int) -> None:
        """cvttsd2si r64, xmm（F2 REX.W 0F 2C /r）"""
        rex = 0x48
        if r64 >= 8: rex |= 1
        if xmm >= 8: rex |= 4
        modrm = 0xC0 | ((r64 & 7) << 3) | (xmm & 7)
        self.emit(0xF2, rex, 0x0F, 0x2C, modrm)

'''
s = s[:end] + sse2 + s[end:]
open(p, "w", encoding="utf-8").write(s)
print("asm SSE2 助手 OK")
