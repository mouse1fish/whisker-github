import struct, zlib
d = open(r"build/live3d.bmp","rb").read()
off = struct.unpack_from("<I", d, 10)[0]
W = struct.unpack_from("<i", d, 18)[0]
H = struct.unpack_from("<i", d, 22)[0]
H2 = abs(H)
rows = []
for y in range(H2):
    src_y = (H2-1-y) if H > 0 else y
    base = off + src_y*W*4
    row = bytearray([0])
    for x in range(W):
        o = base + x*4
        row += bytes((d[o+2], d[o+1], d[o]))
    rows.append(bytes(row))
raw = b"".join(rows)
def chunk(t, data):
    c = t + data
    return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W, H2, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b"")
open(r"build/live3d.png","wb").write(png)
print(f"实况截图 {W}x{H2} -> PNG {len(png)} 字节")
