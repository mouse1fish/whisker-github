import struct

def field_writes(path):
    data = open(path, "rb").read()
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    entry_rva = struct.unpack_from("<I", data, e_lfanew + 24 + 16)[0]
    sec_off = e_lfanew + 24 + 240
    name, vsz, va, rsz, ptr = struct.unpack_from("<8sIIII", data, sec_off)
    off = ptr + (entry_rva - va)
    body = data[off:off+1400]
    out = []
    i = 0
    while i < len(body) - 10:
        if body[i:i+3] == bytes([0x48,0xC7,0x83]):
            disp = struct.unpack_from("<I", body, i+3)[0]
            imm = struct.unpack_from("<I", body, i+7)[0]
            out.append((disp, imm))
            i += 11
        else:
            i += 1
    return out

w1 = field_writes(r"build/wkcc.exe")
w2 = field_writes(r"build/wkcc2.exe")
print(f"wkcc.exe 字段写 {len(w1)} 条 | wkcc2.exe 字段写 {len(w2)} 条")
for i in range(max(len(w1), len(w2))):
    a = w1[i] if i < len(w1) else None
    b = w2[i] if i < len(w2) else None
    if a != b:
        print(f"第 {i} 条不同: wkcc={a and (hex(a[0]), hex(a[1]))} wkcc2={b and (hex(b[0]), hex(b[1]))}")
        if i > 3:
            print("  前一条:", w1[i-1] and (hex(w1[i-1][0]), hex(w1[i-1][1])), b and w2[i-1])
