# -*- coding: utf-8 -*-
"""对比两个 PE 的 IAT 区与导入 hint 表。用法: python tools/cmp_iat.py <exe1> <exe2>"""
import struct, sys

def dump(path):
    data = open(path, "rb").read()
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    coff = e_lfanew + 4
    opt_size = struct.unpack_from("<H", data, coff + 16)[0]
    sec_off = coff + 20 + opt_size
    nsec = struct.unpack_from("<H", data, coff + 2)[0]
    secs = []
    for i in range(nsec):
        so = sec_off + i * 40
        name = data[so:so + 8].rstrip(b"\0").decode()
        vsize, vaddr, rawsize, rawptr = struct.unpack_from("<IIII", data, so + 8)
        secs.append((name, vaddr, vsize, rawptr, rawsize))

    def r2o(rva):
        for name, vaddr, vsize, rawptr, rawsize in secs:
            if vaddr <= rva < vaddr + max(vsize, rawsize):
                return rawptr + (rva - vaddr)
        return None

    print(f"=== {path.split(chr(92))[-1]} ===")
    # IAT 区 0x25300 起 16 槽
    o = r2o(0x25300)
    for slot in range(16):
        v = struct.unpack_from("<Q", data, o + slot * 8)[0]
        if v:
            print(f"  IAT[{slot}] @0x{0x25300+slot*8:X} = 0x{v:X} (hint RVA)")
    # ILT 区（.rdata 内 impBase+40 = RT_RDATA_LEN(482)+40 → rdata RVA 0x11000+522=0x1120A）
    o2 = r2o(0x1120A)
    print("  ILT:")
    for j in range(15):
        v = struct.unpack_from("<I", data, o2 + j * 8)[0]
        # 读 hint 字符串（+2 跳过 hint 版本号）
        so2 = r2o(v)
        nm = ""
        if so2:
            k = so2 + 2
            while data[k] != 0:
                nm += chr(data[k]); k += 1
        print(f"    ILT[{j}] = 0x{v:X} → {nm}")
    # 字面量表
    o3 = r2o(0x1120A + 8 * 16)
    dll = data[o3:o3+13]
    print(f"  dll name @ILT尾: {dll!r}")
    p = o3 + 13
    for j in range(15):
        w = struct.unpack_from("<H", data, p)[0]
        k = p + 2
        nm = ""
        while data[k] != 0:
            nm += chr(data[k]); k += 1
        print(f"    lit[{j}] = {nm}")
        p = k + 1

dump(r"H:\trea-xiancheng-bianyiqi\build\wkcc2.exe")
