import struct
data = open(r"build/wkcc2.exe","rb").read()
blob = open(r"build/rt_blob.bin","rb").read()
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
sec_off = e_lfanew + 24 + 240
# .data 是第 3 个段
name, vsz, va, rsz, ptr = struct.unpack_from("<8sIIII", data, sec_off + 80)
print(f".data va=0x{va:X} vsz=0x{vsz:X} rsz=0x{rsz:X} ptr=0x{ptr:X}")
d = data[ptr:ptr+17984]
b = blob[4715:4715+17984]
print("blob data 全量一致:", d == b)
if d != b:
    for i in range(0, 17984, 8):
        if d[i:i+8] != b[i:i+8]:
            print(f"  首个差异 @data+{i} (RVA 0x{0x21000+i:X}): exe={d[i:i+8].hex()} blob={b[i:i+8].hex()}")
            break
print("g_qhead (data+32) exe:", d[32:40].hex(), "| blob:", b[32:40].hex())
print("g_heap_ptr (data+16) exe:", d[16:24].hex(), "| blob:", b[16:24].hex())
