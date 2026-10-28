# -*- coding: utf-8 -*-
"""反汇编 wkcc.exe（Python 编译器产物）指定 RVA 附近的字节。
用法: python tools/disasm_at.py <rva_hex> [before] [after]
"""
import struct, sys

PATH = r"H:\trea-xiancheng-bianyiqi\build\wkcc.exe"
data = open(PATH, "rb").read()

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
coff = e_lfanew + 4
nsec = struct.unpack_from("<H", data, coff + 2)[0]
opt_size = struct.unpack_from("<H", data, coff + 16)[0]
opt = coff + 20
sec_off = opt + opt_size
sections = []
for i in range(nsec):
    so = sec_off + i * 40
    name = data[so:so + 8].rstrip(b"\0").decode()
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, so + 8)
    sections.append((name, vaddr, vsize, rawptr, rawsize))
    print(f"  {name}: RVA=0x{vaddr:X} VSize=0x{vsize:X} Raw=0x{rawptr:X}")

def rva2off(rva):
    for name, vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    return None

rva = int(sys.argv[1], 16)
before = int(sys.argv[2]) if len(sys.argv) > 2 else 96
after = int(sys.argv[3]) if len(sys.argv) > 3 else 16

# 线性反汇编从 rva-before 开始（简单解码 E8/E9/0F 8x/常见 48 前缀）
start = rva - before
off = rva2off(start)
code = data[off:off + before + after]
print(f"--- RVA 0x{start:X} .. 0x{rva+after:X} ---")

REGS = ["rax","rcx","rdx","rbx","rsp","rbp","rsi","rdi"]
pc = 0
while pc < len(code):
    r = start + pc
    mark = " <<<" if r == rva else ""
    b = code[pc]
    if b == 0xE8 and pc + 5 <= len(code):
        rel = struct.unpack_from("<i", code, pc + 1)[0]
        print(f"0x{r:05X}: E8 {rel:+d}  call 0x{r+5+rel:X}{mark}")
        pc += 5; continue
    if b == 0xE9 and pc + 5 <= len(code):
        rel = struct.unpack_from("<i", code, pc + 1)[0]
        print(f"0x{r:05X}: E9 {rel:+d}  jmp 0x{r+5+rel:X}{mark}")
        pc += 5; continue
    if b == 0x0F and 0x80 <= code[pc+1] <= 0x8F and pc + 6 <= len(code):
        rel = struct.unpack_from("<i", code, pc + 2)[0]
        cc = {4:"e",5:"ne",12:"l",13:"ge",14:"le",15:"g",3:"ae",2:"b",6:"be",7:"a"}.get(code[pc+1]-0x80,"?")
        print(f"0x{r:05X}: 0F {code[pc+1]:02X} {rel:+d}  j{cc} 0x{r+6+rel:X}{mark}")
        pc += 6; continue
    if b == 0x48 and pc + 3 <= len(code):
        b2 = code[pc+1]
        modrm = code[pc+2]
        if b2 == 0x89 or b2 == 0x8B:
            mod = modrm >> 6; rg = (modrm >> 3) & 7; rm = modrm & 7
            if mod == 3:
                d = f"mov {REGS[rm]}, {REGS[rg]}" if b2 == 0x89 else f"mov {REGS[rg]}, {REGS[rm]}"
                print(f"0x{r:05X}: 48 {b2:02X} {modrm:02X}  {d}{mark}"); pc += 3; continue
            if mod == 1 and pc + 4 <= len(code):
                disp = struct.unpack_from("<b", code, pc + 3)[0]
                d = f"mov [{REGS[rm]}{disp:+d}], {REGS[rg]}" if b2 == 0x89 else f"mov {REGS[rg]}, [{REGS[rm]}{disp:+d}]"
                print(f"0x{r:05X}: 48 {b2:02X} {modrm:02X} {disp&0xFF:02X}  {d}{mark}"); pc += 4; continue
            if mod == 2 and pc + 7 <= len(code):
                disp = struct.unpack_from("<i", code, pc + 3)[0]
                d = f"mov [{REGS[rm]}{disp:+d}], {REGS[rg]}" if b2 == 0x89 else f"mov {REGS[rg]}, [{REGS[rm]}{disp:+d}]"
                print(f"0x{r:05X}: 48 {b2:02X} {modrm:02X}  {d} (disp={disp}){mark}"); pc += 7; continue
        if b2 == 0x0F and pc + 4 <= len(code):
            if code[pc+2] == 0xAF:
                modrm = code[pc+3]
                rg = (modrm >> 3) & 7; rm = modrm & 7
                if modrm >> 6 == 3:
                    print(f"0x{r:05X}: 48 0F AF {modrm:02X}  imul {REGS[rg]}, {REGS[rm]}{mark}"); pc += 4; continue
        if b2 in (0x85,) and pc + 3 <= len(code):
            modrm = code[pc+2]
            if modrm >> 6 == 3:
                rg = (modrm >> 3) & 7; rm = modrm & 7
                print(f"0x{r:05X}: 48 85 {modrm:02X}  test {REGS[rg]}, {REGS[rm]}{mark}"); pc += 3; continue
        if b2 == 0x3B and pc + 3 <= len(code):
            modrm = code[pc+2]
            if modrm >> 6 == 3:
                rg = (modrm >> 3) & 7; rm = modrm & 7
                print(f"0x{r:05X}: 48 3B {modrm:02X}  cmp {REGS[rg]}, {REGS[rm]}{mark}"); pc += 3; continue
        if b2 == 0x39 and pc + 3 <= len(code):
            modrm = code[pc+2]
            if modrm >> 6 == 3:
                rg = (modrm >> 3) & 7; rm = modrm & 7
                print(f"0x{r:05X}: 48 39 {modrm:02X}  cmp {REGS[rm]}, {REGS[rg]}{mark}"); pc += 3; continue
    if b == 0x0F and code[pc+1] in (0xB6, 0xB7) and pc + 4 <= len(code):
        modrm = code[pc+2]
        mod = modrm >> 6; rg = (modrm >> 3) & 7; rm = modrm & 7
        rex = 0x48 if b == 0x0F else 0x40
        if mod == 1 and pc + 4 <= len(code):
            disp = struct.unpack_from("<b", code, pc + 3)[0]
            print(f"0x{r:05X}: 0F {code[pc+1]:02X} {modrm:02X} {disp&0xFF:02X}  movzx {REGS[rg]}, byte [{REGS[rm]}{disp:+d}]{mark}")
            pc += 4; continue
        if mod == 2 and pc + 7 <= len(code):
            disp = struct.unpack_from("<i", code, pc + 3)[0]
            print(f"0x{r:05X}: 48 0F {code[pc+1]:02X} {modrm:02X}  movzx {REGS[rg]}, byte [{REGS[rm]}{disp:+d}]{mark}")
            pc += 7; continue
    if b == 0x50 + (0 if True else 0) and 0x50 <= b <= 0x57:
        print(f"0x{r:05X}: {b:02X}  push {REGS[b-0x50]}{mark}"); pc += 1; continue
    if 0x58 <= b <= 0x5F:
        print(f"0x{r:05X}: {b:02X}  pop {REGS[b-0x58]}{mark}"); pc += 1; continue
    if b == 0xC3:
        print(f"0x{r:05X}: C3  ret{mark}"); pc += 1; continue
    if b == 0x48 and code[pc+1] == 0x81 and pc + 7 <= len(code):
        modrm = code[pc+2]
        if modrm >> 6 == 3:
            op = {0:"add",5:"sub",7:"cmp"}.get((modrm >> 3) & 7, "op")
            imm = struct.unpack_from("<i", code, pc + 3)[0]
            print(f"0x{r:05X}: 48 81 {modrm:02X}  {op} {REGS[modrm&7]}, {imm}{mark}"); pc += 7; continue
    print(f"0x{r:05X}: {b:02X}  ??{mark}")
    pc += 1
