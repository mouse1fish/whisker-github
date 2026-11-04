blob = open(r"build/rt_blob.bin","rb").read()
off = 682   # OFF_SEND
code = blob[off:off+90]
print("rt_send (blob+682):")
for i in range(0, 90, 16):
    print(f"  +{i:3d}: " + code[i:i+16].hex(" "))
# 逐字节标注 +55 位置
print(f"  +55 处字节: {code[55:55+8].hex(' ')}")
