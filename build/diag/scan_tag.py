import struct
data = open(r"build/selfhost.exe","rb").read()
# 用户代码区：.text 从 RVA 0x3000（USER_OFF=8192）起，文件偏移 512 + ...
# 扫描整个 .text 找 48 C7 00 imm32（mov qword [rax], imm32）
start = 0x200 + 0x3000 - 0x1000
end = start + 0x10000
i = start
found = 0
while i < end - 7:
    if data[i] == 0x48 and data[i+1] == 0xC7 and data[i+2] == 0x00:
        imm = struct.unpack_from("<i", data, i+3)[0]
        rva = 0x1000 + (i - 0x200)
        print(f"@RVA 0x{rva:X}: mov qword [rax], {imm}")
        found += 1
    i += 1
print("共", found, "处")
