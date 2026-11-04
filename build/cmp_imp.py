import struct
def dump_imports(path, label):
    d = open(path, "rb").read()
    e = struct.unpack_from("<I", d, 0x3C)[0]
    opt = e + 24
    imp_rva, imp_sz = struct.unpack_from("<II", d, opt + 112 + 8)
    secs = []
    for i in range(5):
        name, vsz, va, rsz, ptr = struct.unpack_from("<8sIIII", d, e + 24 + 240 + 40*i)
        secs.append((name.rstrip(b"\0").decode(errors="replace"), va, vsz, rsz, ptr))
        if name.startswith(b"\0"): break
    def r2o(rva):
        for nm, va, vsz, rsz, ptr in secs:
            if va <= rva < va + max(vsz, rsz):
                return ptr + (rva - va)
        return None
    print(f"==== {label} ==== import_dir=0x{imp_rva:X} size={imp_sz}")
    off = r2o(imp_rva)
    di = 0
    while True:
        oft, tds, fwd, nm_rva, ft = struct.unpack_from("<IIIII", d, off + 20*di)
        if oft == 0 and nm_rva == 0:
            print(f"  [desc{di}] TERMINATOR"); break
        o = r2o(nm_rva)
        nm = d[o:o+16].split(b"\0")[0].decode() if o else "??"
        print(f"  [desc{di}] {nm:14s} oft=0x{oft:X} ft=0x{ft:X}")
        # 前 3 个 ILT 项
        io = r2o(oft)
        if io:
            for k in range(3):
                ent = struct.unpack_from("<Q", d, io + 8*k)[0]
                if ent == 0: break
                ho = r2o(ent & 0x7FFFFFFF)
                hn = d[ho+2:ho+2+20].split(b"\0")[0].decode(errors="replace") if ho else "??"
                print(f"        slot{k} -> {hn}")
        di += 1
        if di > 8: break
dump_imports(r"build/wkcc.exe", "wkcc.exe（Python 表，能写产物）")
dump_imports(r"build/wkcc2.exe", "wkcc2.exe（自举表，写产物失败）")
