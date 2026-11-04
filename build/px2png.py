# Raw BGRA -> PNG（纯 Python，无依赖）
import struct, zlib, sys, os

def raw_to_png(raw_path, png_path, W, H):
    d = open(raw_path, "rb").read()
    assert len(d) == W*H*4, f"尺寸不符: {len(d)}"
    rows = []
    for y in range(H):
        row = bytearray([0])
        base = y*W*4
        for x in range(W):
            o = base + x*4
            b, g, r = d[o], d[o+1], d[o+2]
            row += bytes((r, g, b))
        rows.append(bytes(row))
    raw = b"".join(rows)
    def chunk(t, data):
        c = t + data
        return struct.pack(">I", len(data)) + c + struct.pack(">I", zlib.crc32(c) & 0xffffffff)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 2, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(raw, 9))
    png += chunk(b"IEND", b"")
    open(png_path, "wb").write(png)
    return len(png)

for i in range(3):
    src = f"build/3d_frame{i}.px"
    dst = f"build/3d_frame{i}.png"
    n = raw_to_png(src, dst, 480, 360)
    # 统计
    d = open(src, "rb").read()
    cols = set()
    for y in range(0, 360, 4):
        for x in range(0, 480, 4):
            o = (y*480+x)*4
            cols.add((d[o], d[o+1], d[o+2]))
    bg = (30, 26, 22)
    nonbg = 0
    xs, ys = [], []
    for y in range(360):
        for x in range(480):
            o = (y*480+x)*4
            c = (d[o], d[o+1], d[o+2])
            if c != bg:
                nonbg += 1
                xs.append(x); ys.append(y)
    span = (min(xs), max(xs), min(ys), max(ys)) if xs else None
    print(f"帧{i}: PNG {n}B | 采样色数 {len(cols)} | 非背景像素 {nonbg} | 覆盖范围 x{span[0]}-{span[1]} y{span[2]}-{span[3]}" if span else f"帧{i}: 空")
