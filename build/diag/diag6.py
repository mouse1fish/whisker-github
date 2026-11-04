import struct
data = open(r"build/wkcc2.exe","rb").read()
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
entry_rva = struct.unpack_from("<I", data, e_lfanew + 24 + 16)[0]
print(f"AddressOfEntryPoint = RVA 0x{entry_rva:X} (用户代码偏移 {entry_rva - 0x3000})")
off = 0x200 + (entry_rva - 0x1000)
# entry 开头 64 字节
print("entry head:", data[off:off+64].hex(" "))
# 崩溃点 0x10FFB 相对 entry 的位置
print(f"0x10FFB - entry = {0x10FFB - entry_rva} 字节")
# entry 全量 dump 前 200 字节
seg = data[off:off+260]
print("entry+0..260:")
for i in range(0, 260, 26):
    print("  ", (entry_rva + i).__format__('X'), seg[i:i+26].hex(" "))
