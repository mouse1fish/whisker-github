# -*- coding: utf-8 -*-
"""在 exe 的用户代码里找 call rt_read_bytes(RVA 0x17B9) 的位置并 dump 上下文。
用法: python tools/find_readbytes.py <exe路径> <用户代码RVA>"""
import struct, sys

PATH = sys.argv[1]
BASE_RVA = int(sys.argv[2]) if len(sys.argv) > 2 else 0x2000
data = open(PATH, "rb").read()

e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
coff = e_lfanew + 4
opt_size = struct.unpack_from("<H", data, coff + 16)[0]
sec_off = coff + 20 + opt_size
nsec = struct.unpack_from("<H", data, coff + 2)[0]
for i in range(nsec):
    so = sec_off + i * 40
    name = data[so:so + 8].rstrip(b"\0").decode()
    vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, so + 8)
    if name == ".text":
        text_vaddr, text_rawptr, text_rawsize = vaddr, rawptr, rawsize

# 用户代码区
u_start = BASE_RVA - text_vaddr + text_rawptr
u_len = text_rawsize - (BASE_RVA - text_vaddr)
u = data[u_start:u_start + u_len]
print(f"用户代码 {u_len} 字节")

TARGET = 0x1BC6 - 0x1000 + 0x1000  # rt_read_bytes blob 偏移 1977 → RVA 0x1000+1977=0x17B9
TARGET = 0x17B9
n = 0
for pc in range(len(u) - 5):
    if u[pc] == 0xE8:
        rel = struct.unpack_from("<i", u, pc + 1)[0]
        site_rva = BASE_RVA + pc
        tgt = site_rva + 5 + rel
        if tgt == TARGET:
            n += 1
            lo = max(0, pc - 64)
            print(f"\n=== call rt_read_bytes @ RVA 0x{site_rva:X} (用户偏移 {pc}) #{n} ===")
            # dump 前 64 字节 + 调用 + 后 16
            seg = u[lo:pc + 16]
            for k in range(0, len(seg), 16):
                addr = BASE_RVA + lo + k
                print(f"  0x{addr:05X}: " + " ".join(f"{b:02x}" for b in seg[k:k+16]))
if n == 0:
    print("未找到 call rt_read_bytes")
