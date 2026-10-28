# -*- coding: utf-8 -*-
"""静态分析 wkcc2.exe：找 0x44CA 函数的所有调用点，检查 rcx 设置。"""
import struct, sys

path = sys.argv[1] if len(sys.argv) > 1 else "build/wkcc2.exe"
data = open(path, "rb").read()

# ---- 最小 PE 解析：RVA -> 文件偏移 ----
pe_off = struct.unpack_from("<I", data, 0x3C)[0]
assert data[pe_off:pe_off+4] == b"PE\0\0", "not PE"
coff = pe_off + 4
nsec = struct.unpack_from("<H", data, coff + 2)[0]
opt_size = struct.unpack_from("<H", data, coff + 16)[0]
opt = coff + 20
image_base = struct.unpack_from("<Q", data, opt + 24)[0]
sec0 = opt + opt_size
sections = []
for i in range(nsec):
    off = sec0 + 40 * i
    name = data[off:off+8].rstrip(b"\0").decode()
    vsize, vaddr, rsize, raddr = struct.unpack_from("<IIII", data, off + 8)
    sections.append((name, vaddr, vsize, raddr, rsize))
    print(f"sec {name:8s} va=0x{vaddr:X} vs=0x{vsize:X} ra=0x{raddr:X}")

def rva2off(rva):
    for name, vaddr, vsize, raddr, rsize in sections:
        if vaddr <= rva < vaddr + vsize:
            return raddr + (rva - vaddr)
    return None

text = next(s for s in sections if s[0] == ".text")
tva, trva, trsize = text[1], text[3], text[4]
tdata = data[trva:trva+trsize]

# ---- 扫描函数序言: push rbp; mov rbp,rsp; sub rsp,N; push rbx; mov rbx,rcx ----
# 55 48 89 E5 48 81 EC xx xx xx xx 53 48 89 CB
PRO = b"\x55\x48\x89\xE5\x48\x81\xEC"
funcs = []
i = 0
while True:
    j = tdata.find(PRO, i)
    if j < 0: break
    # 检查后续 push rbx; mov rbx,rcx
    if tdata[j+11:j+15] == b"\x53\x48\x89\xCB":
        funcs.append(j)
    i = j + 1
print(f"共 {len(funcs)} 个 def/handler 序言")

CRASH_FN = 0x44CA - tva
# 0x44DA 所在函数
owner = None
for f in funcs:
    if f <= CRASH_FN:
        owner = f
    else:
        break
print(f"0x44CA 所属函数: RVA=0x{owner+tva:X} (文件内偏移 0x{owner:X})")
if owner + tva != 0x44CA:
    # 打印函数头 32 字节
    print("函数头字节:", " ".join(f"{b:02X}" for b in tdata[owner:owner+32]))

# ---- 全文扫描 E8 rel32 调用点，目标 = 0x44CA ----
TARGET = CRASH_FN  # .text 内偏移
callers = []
for k in range(len(tdata) - 5):
    if tdata[k] == 0xE8:
        rel = struct.unpack_from("<i", tdata, k+1)[0]
        tgt = k + 5 + rel
        if tgt == TARGET:
            callers.append(k)
print(f"\n调用 0x{owner+tva:X} 的 call 指令共 {len(callers)} 处：")
for k in callers:
    ctx = tdata[max(0,k-12):k+5]
    print(f"  call@RVA 0x{k+tva:X}  前置字节: " + " ".join(f"{b:02X}" for b in ctx))
