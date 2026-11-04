import struct

def entry_bytes(path):
    data = open(path, "rb").read()
    e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
    entry_rva = struct.unpack_from("<I", data, e_lfanew + 24 + 16)[0]
    sec_off = e_lfanew + 24 + 240
    name, vsz, va, rsz, ptr = struct.unpack_from("<8sIIII", data, sec_off)
    off = ptr + (entry_rva - va)
    return entry_rva, data[off:off+1200]

r1, e1 = entry_bytes(r"build/wkcc.exe")
r2, e2 = entry_bytes(r"build/wkcc2.exe")
print(f"wkcc.exe  entry RVA 0x{r1:X} 长度区段 {len(e1)}")
print(f"wkcc2.exe entry RVA 0x{r2:X} 长度区段 {len(e2)}")
# 找第一个差异
for i in range(min(len(e1), len(e2))):
    if e1[i] != e2[i]:
        print(f"首个差异 @entry+{i} (0x{i:X}):")
        print(f"  wkcc.exe : {e1[max(0,i-8):i+16].hex(' ')}")
        print(f"  wkcc2.exe: {e2[max(0,i-8):i+16].hex(' ')}")
        break
else:
    print("前 1200 字节完全一致")
# 各自 entry 里的 rt_actor_new 的 mov rdx,size 立即数
for nm, e, r in (("wkcc.exe", e1, r1), ("wkcc2.exe", e2, r2)):
    # 找 48 c7 c2 (mov rdx, imm32)
    for i in range(len(e)-7):
        if e[i:i+3] == bytes([0x48,0xC7,0xC2]):
            print(f"  {nm}: mov rdx,imm32 @entry+0x{i:X} imm=0x{struct.unpack_from('<I', e, i+3)[0]:X}")
            break
