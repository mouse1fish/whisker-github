import struct, sys
data = open(r"build/wkcc2.exe", "rb").read()
# PE header parse
e_lfanew = struct.unpack_from("<I", data, 0x3C)[0]
opt_off = e_lfanew + 24
import_rva, import_size = struct.unpack_from("<II", data, opt_off + 112 + 8*1)
iat_rva, iat_size = struct.unpack_from("<II", data, opt_off + 112 + 8*12)
sec_off = e_lfanew + 24 + 240
secs = []
for i in range(3):
    name, vsz, va, rsz, ptr = struct.unpack_from("<8sIIII", data, sec_off + 40*i)
    secs.append((name.rstrip(b"\0").decode(), va, vsz, rsz, ptr))
    print(f"sec {name.rstrip(chr(0).encode()).decode():8s} va=0x{va:X} vsz=0x{vsz:X} rawsz=0x{rsz:X} ptr=0x{ptr:X}")
print(f"import dir rva=0x{import_rva:X} size=0x{import_size:X} | iat rva=0x{iat_rva:X} size=0x{iat_size:X}")
def rva2off(rva):
    for name, va, vsz, rsz, ptr in secs:
        if va <= rva < va + max(vsz, rsz):
            return ptr + (rva - va)
    return None
off = rva2off(import_rva)
di = 0
while True:
    oft, tds, fwd, name_rva, ft = struct.unpack_from("<IIIII", data, off + 20*di)
    if oft == 0 and name_rva == 0:
        print(f"[desc {di}] TERMINATOR")
        break
    nm = data[rva2off(name_rva):rva2off(name_rva)+20].split(b"\0")[0].decode()
    print(f"[desc {di}] dll={nm} oft=0x{oft:X} ft=0x{ft:X}")
    if "ws2" in nm or di == 0:
        # walk ILT
        ilt_off = rva2off(oft)
        for k in range(40):
            e = struct.unpack_from("<Q", data, ilt_off + 8*k)[0]
            if e == 0: break
            hn = data[rva2off(e & 0x7FFFFFFF):rva2off(e & 0x7FFFFFFF)+40]
            fn = hn[2:].split(b"\0")[0].decode(errors="replace")
            print(f"    slot{k:2d} -> {fn}")
    di += 1
# crash bytes at RVA 0x13bf
coff = rva2off(0x13bf)
print("bytes @0x13bf:", data[coff:coff+24].hex(" "))
