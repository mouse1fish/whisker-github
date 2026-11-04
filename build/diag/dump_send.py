data = open(r"build/selfhost.exe","rb").read()
def dump(rva, n=64):
    off = 0x200 + (rva - 0x1000)
    print(f"--- RVA 0x{rva:X} ---")
    for i in range(0, n, 16):
        print(f"  +{i:02X}: " + data[off+i:off+i+16].hex(" "))
dump(0x32A0, 96)
