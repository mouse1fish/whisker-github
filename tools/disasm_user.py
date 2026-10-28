# -*- coding: utf-8 -*-
"""反汇编 selfhost.exe 用户代码区（RVA 0x2000 起），核对 call/jmp 目标。"""
import struct, sys

PATH = r"H:\trea-xiancheng-bianyiqi\build\selfhost.exe"

data = open(PATH, "rb").read()

# ---- 解析 PE 头 ----
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
assert data[e_lfanew:e_lfanew+4] == b"PE\0\0", "PE 签名错误"
coff = e_lfanew + 4
nsec = struct.unpack_from("<H", data, coff+2)[0]
opt_size = struct.unpack_from("<H", data, coff+16)[0]
opt = coff + 20
entry_rva = struct.unpack_from("<I", data, opt+16)[0]
image_base = struct.unpack_from("<Q", data, opt+24)[0]
print(f"entry RVA = 0x{entry_rva:X}, ImageBase = 0x{image_base:X}")

# 段表
sec_off = opt + opt_size
sections = []
for i in range(nsec):
    so = sec_off + i*40
    name = data[so:so+8].rstrip(b"\0").decode()
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, so+8)
    sections.append((name, vaddr, vsize, rawptr, rawsize))
    print(f"  {name}: RVA=0x{vaddr:X} VSize=0x{vsize:X} Raw=0x{rawptr:X} RawSize=0x{rawsize:X}")

def rva2off(rva):
    for name, vaddr, vsize, rawptr, rawsize in sections:
        if vaddr <= rva < vaddr + max(vsize, rawsize):
            return rawptr + (rva - vaddr)
    return None

# ---- 用户代码区 ----
USER_RVA = 0x2000
uoff = rva2off(USER_RVA)
print(f"用户代码文件偏移 = 0x{uoff:X}")
code = data[uoff:uoff+4096]

REGS64 = ["rax","rcx","rdx","rbx","rsp","rbp","rsi","rdi"]
REGS8X = ["r8","r9","r10","r11","r12","r13","r14","r15"]

pc = 0  # 用户代码内偏移
end = 900
while pc < end:
    rva = USER_RVA + pc
    b = code[pc]
    # 尝试解码常见形态
    # E8 rel32 call
    if b == 0xE8 and pc+5 <= len(code):
        rel = struct.unpack_from("<i", code, pc+1)[0]
        target = rva + 5 + rel
        kind = "RT" if target < USER_RVA else "USER"
        print(f"{pc:5d} (0x{rva:05X}): E8 {rel:+9d}  -> call {kind} 0x{target:X}")
        pc += 5
        continue
    # FF 15 rel32 call [rip+..]
    if b == 0xFF and code[pc+1] == 0x15 and pc+6 <= len(code):
        rel = struct.unpack_from("<i", code, pc+2)[0]
        target = rva + 6 + rel
        print(f"{pc:5d} (0x{rva:05X}): FF 15 {rel:+8d} -> call [0x{target:X}]  (IAT?)")
        pc += 6
        continue
    # E9 rel32 jmp
    if b == 0xE9 and pc+5 <= len(code):
        rel = struct.unpack_from("<i", code, pc+1)[0]
        target = rva + 5 + rel
        print(f"{pc:5d} (0x{rva:05X}): E9 {rel:+9d}  -> jmp 0x{target:X}")
        pc += 5
        continue
    # 0F 8x rel32 jcc
    if b == 0x0F and 0x80 <= code[pc+1] <= 0x8F and pc+6 <= len(code):
        rel = struct.unpack_from("<i", code, pc+2)[0]
        target = rva + 6 + rel
        cc = code[pc+1] - 0x80
        ccn = {0:"o",1:"no",2:"b",3:"ae",4:"e",5:"ne",6:"be",7:"a",8:"s",9:"ns",10:"p",11:"np",12:"l",13:"ge",14:"le",15:"g"}[cc]
        print(f"{pc:5d} (0x{rva:05X}): 0F {code[pc+1]:02X} {rel:+8d} -> j{ccn} 0x{target:X}")
        pc += 6
        continue
    # 48 8D xx (lea)
    if b == 0x48 and code[pc+1] == 0x8D and pc+7 <= len(code):
        modrm = code[pc+2]
        if (modrm >> 6) == 0 and (modrm & 7) == 5:
            rel = struct.unpack_from("<i", code, pc+3)[0]
            target = rva + 7 + rel
            reg = REGS64[(modrm >> 3) & 7]
            print(f"{pc:5d} (0x{rva:05X}): 48 8D {modrm:02X} {rel:+8d} -> lea {reg}, [0x{target:X}]")
            pc += 7
            continue
    # 48 C7 xx imm32 (mov reg, imm32 / mov [..], imm32)
    if b == 0x48 and code[pc+1] == 0xC7 and pc+7 <= len(code):
        modrm = code[pc+2]
        mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
        if mod == 3:
            imm = struct.unpack_from("<i", code, pc+3)[0]
            print(f"{pc:5d} (0x{rva:05X}): 48 C7 {modrm:02X}       -> mov {REGS64[rm]}, {imm}")
            pc += 7
            continue
        if mod == 0 and rm == 0:
            imm = struct.unpack_from("<i", code, pc+3)[0]
            print(f"{pc:5d} (0x{rva:05X}): 48 C7 {modrm:02X}       -> mov qword [rax], {imm}")
            pc += 7
            continue
        if mod == 1 and rm == 0:
            disp = code[pc+3]
            imm = struct.unpack_from("<i", code, pc+4)[0]
            print(f"{pc:5d} (0x{rva:05X}): 48 C7 {modrm:02X}       -> mov qword [rax+{disp}], {imm}")
            pc += 8
            continue
    # 48 8B xx (mov r64, r/m64)
    if b == 0x48 and code[pc+1] == 0x8B and pc+3 <= len(code):
        modrm = code[pc+2]
        mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
        if mod == 3:
            print(f"{pc:5d} (0x{rva:05X}): 48 8B {modrm:02X}       -> mov {REGS64[reg]}, {REGS64[rm]}")
            pc += 3
            continue
        if mod == 0 and rm in (0,2,4):
            if rm == 4:  # SIB
                sib = code[pc+3]
                if (sib & 7) == 4 and ((sib>>3)&7) == 4:
                    disp = struct.unpack_from("<i", code, pc+4)[0]
                    print(f"{pc:5d} (0x{rva:05X}): 48 8B {modrm:02X} {sib:02X}    -> mov {REGS64[reg]}, [rsp{disp:+d}]")
                    pc += 8
                    continue
            else:
                print(f"{pc:5d} (0x{rva:05X}): 48 8B {modrm:02X}       -> mov {REGS64[reg]}, [{REGS64[rm]}]")
                pc += 3
                continue
        if mod == 1 and rm == 4:
            sib = code[pc+3]; disp = code[pc+4]
            print(f"{pc:5d} (0x{rva:05X}): 48 8B {modrm:02X} {sib:02X} {disp:02X} -> mov {REGS64[reg]}, [rsp{disp:+d}]")
            pc += 5
            continue
        if mod == 1:
            disp = struct.unpack_from("<b", code, pc+3)[0]
            print(f"{pc:5d} (0x{rva:05X}): 48 8B {modrm:02X}       -> mov {REGS64[reg]}, [{REGS64[rm]}{disp:+d}]")
            pc += 4
            continue
        if mod == 2:
            disp = struct.unpack_from("<i", code, pc+3)[0]
            print(f"{pc:5d} (0x{rva:05X}): 48 8B {modrm:02X}       -> mov {REGS64[reg]}, [{REGS64[rm]}{disp:+d}]")
            pc += 7
            continue
    # 48 89 xx (mov r/m64, r64)
    if b == 0x48 and code[pc+1] == 0x89 and pc+3 <= len(code):
        modrm = code[pc+2]
        mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
        if mod == 3:
            print(f"{pc:5d} (0x{rva:05X}): 48 89 {modrm:02X}       -> mov {REGS64[rm]}, {REGS64[reg]}")
            pc += 3
            continue
    # 48 83 xx imm8
    if b == 0x48 and code[pc+1] == 0x83 and pc+4 <= len(code):
        modrm = code[pc+2]
        mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
        if mod == 3:
            imm = struct.unpack_from("<b", code, pc+3)[0]
            op = {0:"add",1:"or",2:"adc",3:"sbb",4:"and",5:"sub",6:"xor",7:"cmp"}[reg]
            print(f"{pc:5d} (0x{rva:05X}): 48 83 {modrm:02X}       -> {op} {REGS64[rm]}, {imm}")
            pc += 4
            continue
    # 48 81 xx imm32 (sub rsp, imm32 等)
    if b == 0x48 and code[pc+1] == 0x81 and pc+7 <= len(code):
        modrm = code[pc+2]
        mod = modrm >> 6; reg = (modrm >> 3) & 7; rm = modrm & 7
        if mod == 3:
            imm = struct.unpack_from("<i", code, pc+3)[0]
            op = {0:"add",1:"or",2:"adc",3:"sbb",4:"and",5:"sub",6:"xor",7:"cmp"}[reg]
            print(f"{pc:5d} (0x{rva:05X}): 48 81 {modrm:02X}       -> {op} {REGS64[rm]}, {imm}")
            pc += 7
            continue
    # 单字节
    simple = {0x55:"push rbp", 0x5D:"pop rbp", 0xC3:"ret", 0x51:"push rcx", 0x52:"push rdx",
              0x90:"nop", 0x5B:"pop rbx", 0x50:"push rax", 0x58:"pop rax"}
    if b in simple:
        print(f"{pc:5d} (0x{rva:05X}): {b:02X}            -> {simple[b]}")
        pc += 1
        continue
    # 未知：hex dump 8 字节
    chunk = code[pc:pc+8].hex(" ")
    print(f"{pc:5d} (0x{rva:05X}): {chunk}  ??")
    pc += 1

print("\n--- 完成 ---")
