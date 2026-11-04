import struct
data = open(r"build/wkcc2.exe", "rb").read()
off = 0x10800 + (0x11394 - 0x11000)   # .rdata raw ptr + (rva - va)
for di in range(3):
    oft, tds, fwd, name_rva, ft = struct.unpack_from("<IIIII", data, off + 20*di)
    print(f"desc{di}: oft=0x{oft:X} name_rva=0x{name_rva:X} ft=0x{ft:X}")
# ILT0 region dump
base = 0x10800 + (ilt := (0x11394 + 60)) - 0x11000 if False else 0x10800 + (0x11394 + 60 - 0x11000)
print("ILT0 first 4 slots:", [hex(struct.unpack_from('<Q', data, base + 8*k)[0]) for k in range(4)])
# what strings live at the expected dll name RVAs?
d0 = 0x10800 + ((0x11394 + 60 + 8*22 + 8*13) - 0x11000)
print("expected dll0 area:", data[d0:d0+40])
