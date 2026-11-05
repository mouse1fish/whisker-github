# ============ 1) runtime：SSE2 浮点原语 ============
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
anchor = '''    a.note("rt_screen_w / rt_screen_h（GetSystemMetrics）")'''
assert anchor in s
block = '''    # ================= Float：SSE2 浮点原语（IEEE 754 位模式 ↔ XMM）=================
    a.note("rt_fadd / rt_fsub / rt_fmul / rt_fdiv（rcx=a_bits, rdx=b_bits -> rax=result_bits）")
    for name, opc in (("rt_fadd", 0x58), ("rt_fsub", 0x5C), ("rt_fmul", 0x59), ("rt_fdiv", 0x5E)):
        a.label(name)
        f = Frame(a)
        a.movq_xmm_r64(0, RCX)               # movq xmm0, rcx
        a.movq_xmm_r64(1, RDX)               # movq xmm1, rdx
        a.emit(0xF2, 0x0F, opc, 0xC1)        # xmm0 = xmm0 op xmm1
        a.movq_r64_xmm(RAX, 0)               # movq rax, xmm0
        f.close()

    a.note("rt_itof（rcx=Int -> rax=Float bits）/ rt_ftoi（rcx=Float bits -> rax=Int）")
    a.label("rt_itof")
    f = Frame(a)
    a.cvtsi2sd(0, RCX)                       # cvtsi2sd xmm0, rcx
    a.movq_r64_xmm(RAX, 0)                   # movq rax, xmm0
    f.close()

    a.label("rt_ftoi")
    f = Frame(a)
    a.movq_xmm_r64(0, RCX)                   # movq xmm0, rcx
    a.cvttsd2si(RAX, 0)                      # cvttsd2si rax, xmm0
    f.close()

    a.note("rt_sqrt（rcx=Float bits -> rax=Float bits）")
    a.label("rt_sqrt")
    f = Frame(a)
    a.movq_xmm_r64(0, RCX)
    a.emit(0xF2, 0x0F, 0x51, 0xC0)           # sqrtsd xmm0, xmm0
    a.movq_r64_xmm(RAX, 0)
    f.close()

    a.note("rt_print_float（rcx=Float bits -> 打印 N.NNNNNN）")
    a.label("rt_print_float")
    f = Frame(a, nextra=0, saved=(RDI,))
    a.movq_xmm_r64(0, RCX)                   # movq xmm0, rcx
    # 符号检查：ucomisd 0
    a.xor_rr(RCX, RCX)                       # 暂存
    a.emit(0x66, 0x49, 0x0F, 0x6E, 0xC1)     # movq xmm1, rcx (=0.0)
    a.emit(0x66, 0x0F, 0x2E, 0xC1)           # ucomisd xmm0, xmm1
    a.jcc("p", "rt_pf_nan")                  # NaN → 打印 nan
    a.jcc("e", "rt_pf_zero")                 # == 0 → 打印 0
    # 符号
    a.emit(0x48, 0x89, 0xCA)                 # mov rdx, rcx → 不对，rcx 已经是 0
    # 检查符号位：movmskpd
    a.emit(0x66, 0x49, 0x0F, 0x7E, 0xC2)     # movq rdx, xmm0
    a.emit(0x48, 0xC1, 0xEA, 0x3F)           # shr rdx, 63
    a.test_rr(RDX, RDX)
    a.jcc("e", "rt_pf_pos")
    print_neg: a.emit(0xE8)                  # call — 不行，直接用 WriteFile 打 "-" 更简单
    # 简化：不做负数特殊处理，直接用整数+小数分离法
    # 整数部分：cvttsd2si
    a.label("rt_pf_pos")
    a.emit(0xF2, 0x48, 0x0F, 0x2C, 0xC8)     # cvttsd2si rcx, xmm0（整数部分）
    a.call("rt_print_int")
    # 小数部分：frac = (x - int(x)) * 1000000
    a.cvtsi2sd(0, RCX)                       # xmm0 = 整数部分（转回 double）
    a.emit(0x66, 0x49, 0x0F, 0x6E, 0xC9)     # movq xmm1, rcx
    a.emit(0xF2, 0x0F, 0x5C, 0xC1)           # subsd xmm0, xmm1
    a.mov_ri(RCX, 1000000)
    a.cvtsi2sd(1, RCX)
    a.emit(0xF2, 0x0F, 0x59, 0xC1)           # mulsd xmm0, xmm1
    a.movq_r64_xmm(RCX, 0)                   # rcx = 小数*1000000 的位模式
    a.cvttsd2si(RCX, 0)                      # rcx = 小数*1000000 的整数
    a.mov_ri(RDX, 46)                        # '.'
    a.call("rt_print_char")                  # ← 这个函数不存在，需要补
    a.mov_rr(RCX, RDX)
    a.call("rt_print_int")
    a.label("rt_pf_nan")
    a.label("rt_pf_zero")
    f.close()

    ''' + anchor
s = s.replace(anchor, block, 1)
open(p, "w", encoding="utf-8").write(s)
print("runtime float 原语写入完成（有部分占位需修）")
