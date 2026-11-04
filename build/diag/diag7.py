data = open(r"build/wkcc2.exe","rb").read()
off = 0x200 + (0x10F95 - 0x1000)
print("dispatch 区 @0x10F95:")
for i in range(0, 80, 20):
    print(f"  +{i:3d}", data[off+i:off+i+20].hex(" "))
