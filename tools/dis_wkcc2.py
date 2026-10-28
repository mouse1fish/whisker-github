# -*- coding: utf-8 -*-
"""反汇编 wkcc2.exe 用户代码指定偏移附近。用法: python tools/dis_wkcc2.py <用户代码偏移>"""
import struct, sys

PATH = r"H:\trea-xiancheng-bianyiqi\build\wkcc2.exe"
data = open(PATH, "rb").read()

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
coff = e_lfanew + 4
opt_size = struct.unpack_from("<H", data, coff + 16)[0]
opt = coff + 20
sec_off = opt + opt_size
nsec = struct.unpack_from("<H", data, coff + 2)[0]
for i in range(nsec):
    so = sec_off + i * 40
    name = data[so:so + 8].rstrip(b"\0").decode()
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, so + 8)
    if name == ".text":
        text_vaddr, text_rawptr = vaddr, rawptr

uoff = int(sys.argv[1])          # 用户代码内偏移
base_rva = 0x2000
file_off = text_rawptr + (base_rva - text_vaddr) + uoff
print(f"用户代码偏移 {uoff} → 文件偏移 0x{file_off:X}, RVA 0x{base_rva+uoff:X}")

code = data[file_off:file_off + 80]
print(" ".join(f"{b:02x}" for b in code[:48]))

REGS = ["rax", "rcx", "rdx", "rbx", "rsp", "rbp", "rsi", "rdi"]
pc = 0
while pc < 48:
    b = code[pc]
    if b == 0x48 and code[pc+1] == 0x81 and code[pc+2] >> 6 == 3 and code[pc+2] & 7 == 7:
        op = {(modrm >> 3) & 7: o for modrm in [code[pc+2]] for o in [0] }  # noop
        opn = {0:"add",5:"sub",7:"cmp"}.get((code[pc+2] >> 3) & 7, "op")
        imm = struct.unpack_from("<i", code, pc + 3)[0]
        print(f"+{pc}: 48 81 {code[pc+2]:02X}  {opn} {REGS[code[pc+2]&7]}, {imm}")
        pc += 7; continue
    if b == 0x48 and code[pc+1] == 0xF7:
        modrm = code[pc+2]
        if modrm >> 6 == 3:
            opn = {6:"idiv",7:"idiv"}.get((modrm >> 3) & 7, "?")
            if (modrm >> 3) & 7 == 7:
                print(f"+{pc}: 48 F7 {modrm:02X}  idiv {REGS[modrm&7]}   <<< 除法")
            else:
                print(f"+{pc}: 48 F7 {modrm:02X}  (F7 /{((modrm>>3)&7)})")
            pc += 3; continue
    if b == 0x48 and code[pc+1] == 0x8B and code[pc+2] >> 6 == 3:
        modrm = code[pc+2]
        print(f"+{pc}: 48 8B {modrm:02X}  mov {REGS[(modrm>>3)&7]}, {REGS[modrm&7]}")
        pc += 3; continue
    if b == 0x48 and code[pc+1] == 0x99:
        print(f"+{pc}: 48 99  cqo")
        pc += 2; continue
    if b == 0x48 and code[pc+1] == 0x89 and code[pc+2] >> 6 == 3:
        modrm = code[pc+2]
        print(f"+{pc}: 48 89 {modrm:02X}  mov {REGS[modrm&7]}, {REGS[(modrm>>3)&7]}")
        pc += 3; continue
    if b == 0x48 and code[pc+1] == 0xC7 and code[pc+2] >> 6 == 3:
        imm = struct.unpack_from("<i", code, pc + 3)[0]
        print(f"+{pc}: 48 C7 {code[pc+2]:02X}  mov {REGS[code[pc+2]&7]}, {imm}")
        pc += 7; continue
    if b == 0xE8:
        rel = struct.unpack_from("<i", code, pc + 1)[0]
        print(f"+{pc}: E8  call {base_rva+uoff+pc+5+rel:#x}")
        pc += 5; continue
    print(f"+{pc}: {b:02x}  ??")
    pc += 1
