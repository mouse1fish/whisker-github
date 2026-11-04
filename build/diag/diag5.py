data = open(r"build/wkcc2.exe","rb").read()
# RVA 0x10FFB -> file: .text ptr=0x200, va=0x1000
off = 0x200 + (0x10FFB - 0x1000)
print("bytes @RVA 0x10FF5:", data[off-6:off+18].hex(" "))
# 向后找函数序言 55 48 89 E5
lo = 0x200
i = off
while i > lo:
    if data[i:i+4] == bytes([0x55, 0x48, 0x89, 0xE5]):
        rva = 0x1000 + (i - 0x200)
        print(f"序言 @file 0x{i:X} = RVA 0x{rva:X} (用户代码偏移 {rva - 0x3000})")
        break
    i -= 1
