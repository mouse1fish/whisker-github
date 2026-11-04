data = open(r"build/wkcc2.exe","rb").read()
blob = open(r"build/rt_blob.bin","rb").read()
# exe .text raw 从 0x200 起；RVA 0x13BF -> file 0x5BF
exe_bytes = data[0x5BF-16:0x5BF+24]
print("exe @0x13BF-16:", exe_bytes.hex(" "))
# blob bin 内 0x3AF..0x3D7
print("blob @0x3AF:", blob[0x3AF:0x3D7].hex(" "))
print("match:", data[0x200+0x3AF:0x200+0x3D7] == blob[0x3AF:0x3D7])
# 全段对比
t = blob[:4715]
print("blob text 全量一致:", data[0x200:0x200+4715] == t)
