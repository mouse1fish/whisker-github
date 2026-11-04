import struct
data = open(r"build/wkcc2.exe","rb").read()
entry = 0x10FC6
targets = {0x102C: "rt_init", 0x1278: "rt_actor_new", 0x1194: "rt_alloc",
           0x129E: "rt_send", 0x150E: "rt_run", 0x110C: "?0x10C", 0x1111: "?"}
# 扫描 entry 后 4KB 内的 E8 rel32
off0 = 0x200 + (entry - 0x1000)
for i in range(off0, off0 + 4096):
    if data[i] == 0xE8:
        rel = struct.unpack_from("<i", data, i+1)[0]
        nxt = 0x1000 + (i - 0x200) + 5
        tgt = nxt + rel
        rva = 0x1000 + (i - 0x200)
        if tgt in (0x102C, 0x1278, 0x1194, 0x129E, 0x150E):
            print(f"call @RVA 0x{rva:X} -> {targets.get(tgt, hex(tgt))} (blob 0x{tgt-0x1000:X})")
    if data[i] == 0xFF and i+1 < len(data) and data[i+1] == 0x15:
        rva = 0x1000 + (i - 0x200)
        rel = struct.unpack_from("<i", data, i+2)[0]
        tgt = 0x1000 + (i - 0x200) + 6 + rel
        print(f"call [IAT] @RVA 0x{rva:X} -> IAT RVA 0x{tgt:X}")
