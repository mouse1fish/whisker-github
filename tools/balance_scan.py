# -*- coding: utf-8 -*-
"""逐函数 push/pop 平衡分析：找函数体内 push/pop 净差非 0 的 def。
用法: python tools/balance_scan.py <exe> [起始RVA(16进制，默认0x1000)]
"""
import struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else "build/wkcc2.exe"
start_rva = int(sys.argv[2], 16) if len(sys.argv) > 2 else 0x1000
data = open(path, "rb").read()

# PE 段
pe = struct.unpack_from("<I", data, 0x3C)[0]
coff = pe + 4
nsec = struct.unpack_from("<H", data, coff + 2)[0]
opt_size = struct.unpack_from("<H", data, coff + 16)[0]
sec0 = coff + 20 + opt_size
segs = []  # (va, vsize, raw)
for i in range(nsec):
    o = sec0 + 40 * i
    vsz, va, rsz, ra = struct.unpack_from("<IIII", data, o + 8)
    segs.append((va, vsz, ra))

def rva2off(rva):
    for va, vsz, ra in segs:
        if va <= rva < va + vsz:
            return ra + (rva - va)
    return None

def byte_at(rva):
    o = rva2off(rva)
    return data[o] if o is not None else None

def modrm_len(rva):  # 返回 modrm+sib+disp 的字节数（不含 opcode）
    m = byte_at(rva); mod = m >> 6; rm = m & 7
    n = 1
    if mod != 3 and rm == 4: n += 1  # sib
    if mod == 0 and rm == 5: return n + 4
    if mod == 1: return n + 1
    if mod == 2: return n + 4
    return n

REX = set(range(0x40, 0x50))

def insn_len(rva):
    """返回指令长度；无法识别返回 None"""
    b0 = byte_at(rva)
    o = rva
    rex = 0
    if b0 in REX:
        rex = b0; o += 1; b0 = byte_at(o)
    # 两字节 0F
    if b0 == 0x0F:
        b1 = byte_at(o + 1)
        if 0x80 <= b1 <= 0x8F: return 6       # jcc rel32
        if 0x90 <= b1 <= 0x9F: return 3       # setcc
        if b1 in (0xB6, 0xB7, 0xBE, 0xBF): return 3 + modrm_len(o + 2)  # movzx/movsx
        if b1 == 0xAF: return 3 + modrm_len(o + 2)  # imul
        if b1 in (0x05, 0x0D): return o - rva + 7  # syscall 不存在，略
        if b1 == 0x1F: return 3 + modrm_len(o + 2)  # nop
        if b1 in (0x10,0x11,0x28,0x29,0x2E,0x6F,0x7F,0x54,0x57,0xEF):  # sse
            return 3 + modrm_len(o + 2)
        return None
    # push/pop
    if 0x50 <= b0 <= 0x5F: return 1
    # jcc rel8 / jmp rel8
    if 0x70 <= b0 <= 0x7F: return 2
    if b0 == 0xEB: return 2
    if b0 == 0xE8 or b0 == 0xE9: return 5
    if b0 == 0xC3 or b0 == 0x90 or b0 == 0xF8 or b0 == 0xF9 or b0 == 0xFC: return 1
    if b0 == 0x98: return 1   # cwde
    if b0 == 0x99: return 1   # cdq (48 99 handled by rex path too)
    # push imm
    if b0 == 0x6A: return 2
    if b0 == 0x68: return 5
    # ALU imm8/imm32 与 grp
    if b0 in (0x80, 0x81, 0x83, 0x88, 0x8A, 0x8B, 0x89, 0x8D, 0xC6, 0xC7,
              0x01,0x03,0x09,0x0B,0x11,0x13,0x19,0x1B,0x21,0x23,0x29,0x2B,
              0x31,0x33,0x39,0x3B,0x85,0x84,0x8D,0xD8,0xD9,0xF7,0xF6,0xFF,0xFE,0x63):
        n = modrm_len(o + 1)
        if b0 == 0x81 or b0 == 0xC7: n += 4
        elif b0 in (0x83, 0xC6): n += 1
        if b0 == 0x8D and rex: pass
        return (o - rva) + 1 + n
    # B8+r imm32（含 48 C7 形式之外）: B8-BF mov eXX, imm32
    if 0xB8 <= b0 <= 0xBF:
        sz = 4 if rex else 4
        return (o - rva) + 1 + sz
    # C1 shift imm8 / D1 shift 1 / D3
    if b0 == 0xC1: return 1 + modrm_len(o + 1) + 1
    if b0 == 0xD1 or b0 == 0xD3: return 1 + modrm_len(o + 1)
    if b0 == 0x0F: return None
    if b0 in (0x24, 0x25, 0x04, 0x05, 0x0C, 0x0D, 0x14, 0x15, 0x1C, 0x1D,
              0x2C, 0x2D, 0x34, 0x35, 0x3C, 0x3D):  # ALU eax, imm
        return (o - rva) + 1 + (4 if b0 & 1 in (1,) and b0 not in (0x24,0x0C,0x14,0x1C,0x2C,0x34,0x3C) else (4 if (b0 & 7) == 5 else 1))
    if b0 in (0x28,0x2A,0x30,0x32,0x38,0x3A):  # 已在上面
        return (o - rva) + 1 + modrm_len(o + 1)
    return None

# 函数序言起点
PRO = b"\x55\x48\x89\xE5\x48\x81\xEC"
base_rva = start_rva
# .text 范围
tva, tvsz, tra = segs[0]
raw = data[tra:tra + tvsz]

funcs = []
i = 0
while True:
    j = raw.find(PRO, i)
    if j < 0: break
    if raw[j + 11] == 0x53 and raw[j + 12:j + 15] == b"\x48\x89\xCB":
        funcs.append(tva + j)
    i = j + 1
# 结尾：下一个函数起点
print(f"函数数: {len(funcs)}")
bad = 0
for fi, f in enumerate(funcs):
    end = funcs[fi + 1] if fi + 1 < len(funcs) else tva + tvsz
    pc = f
    push = pop = 0
    unknown = 0
    sites = []
    while pc < end:
        b = byte_at(pc)
        if b == 0xC3:  # ret — 函数可能提前结束
            pc += 1
            # 继续扫（后面可能还有别的分支的 ret），直到 end
            continue
        L = insn_len(pc)
        if L is None:
            unknown += 1
            pc += 1
            continue
        b0 = byte_at(pc)
        rex = byte_at(pc) if byte_at(pc) in REX else 0
        if 0x50 <= b0 <= 0x57 or (rex and 0x40 | 0 <= rex <= 0x4F and 0x50 <= b0 <= 0x57):
            push += 1
            sites.append((pc, "push"))
        elif 0x58 <= b0 <= 0x5F:
            pop += 1
            sites.append((pc, "pop"))
        elif rex in REX and byte_at(pc + 1) is not None and 0x50 <= byte_at(pc + 1) <= 0x5F:
            # REX + push/pop（48 55 等不常见）
            if byte_at(pc + 1) <= 0x57: push += 1; sites.append((pc, "push"))
            else: pop += 1; sites.append((pc, "pop"))
        pc += L
    if push != pop:
        bad += 1
        # 找函数名
        print(f"\n== 不平衡: RVA 0x{f:X}  push={push} pop={pop} (net {push-pop})  unknown_bytes={unknown}")
        # 打印全部 push/pop 位点
        for s, k in sites:
            print(f"     {k} @ 0x{s:X}")
if bad == 0:
    print("所有函数 push/pop 平衡 ✓")
