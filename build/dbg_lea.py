import struct
blob = open(r"build/rt_blob.bin","rb").read()
RT_DATA_OFF = 9146
DATA_RVA = 0x31000
CODE_RVA = 0x1000

# 1) rt_sin16 完整体（从 5142 起 40 字节）
off = 5142
code = blob[off:off+40]
print("rt_sin16:", code.hex(" "))
# 找 lea（48 8D 05 + rel32）
i = code.find(b"\x48\x8d\x05")
rel = struct.unpack_from("<i", code, i+3)[0]
next_rva = CODE_RVA + off + i + 7
target = next_rva + rel
print(f"lea 位于 text+{off+i}（RVA 0x{next_rva:X}）rel={rel} -> 目标 RVA 0x{target:X}（data 内偏移 {target - DATA_RVA}）")

# 2) 在 data 段找正弦表（table[1]≈1608）
tbl = []
import math
for k in range(1,5):
    tbl.append(int(round(math.sin(k*2*math.pi/256)*65536)))
pat = b"".join(struct.pack("<i", v) for v in tbl)
found = blob.find(pat, RT_DATA_OFF)
print(f"正弦表 table[1..4] 实际位置: data 内偏移 {found - RT_DATA_OFF if found>=0 else '未找到'} (RVA 0x{DATA_RVA + (found-RT_DATA_OFF):X})" if found>=0 else "未找到表")
