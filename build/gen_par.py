import math

# 生成 cube3d_par.wk —— 12 Band actor 并行渲染（内联展开版）
NB = 12
ONE = 65536
FOCAL = 420 * ONE
CAMZ = 4 * ONE

# Band actor 的公共引擎 defs（从 cube3d.wk 提取）
band_engine = """    # ---- 引擎逻辑（每个 Band 独立执行）----
    def initCube {
        i: Int = 0
        while i < 8 {
            s1: Int = 1
            if i % 2 == 1 { s1 = -1 }
            s2: Int = 1
            if (i / 2) % 2 == 1 { s2 = -1 }
            s3: Int = 1
            if (i / 4) % 2 == 1 { s3 = -1 }
            vx[i] = s1 * ONE
            vy[i] = s2 * ONE
            vz[i] = s3 * ONE
            i = i + 1
        }
        fv[0] = 4
        fv[1] = 5
        fv[2] = 6
        fv[3] = 4
        fv[4] = 6
        fv[5] = 7
        fv[6] = 1
        fv[7] = 0
        fv[8] = 3
        fv[9] = 1
        fv[10] = 3
        fv[11] = 2
        fv[12] = 0
        fv[13] = 4
        fv[14] = 7
        fv[15] = 0
        fv[16] = 7
        fv[17] = 3
        fv[18] = 5
        fv[19] = 1
        fv[20] = 2
        fv[21] = 5
        fv[22] = 2
        fv[23] = 6
        fv[24] = 7
        fv[25] = 6
        fv[26] = 2
        fv[27] = 7
        fv[28] = 2
        fv[29] = 3
        fv[30] = 0
        fv[31] = 1
        fv[32] = 5
        fv[33] = 0
        fv[34] = 5
        fv[35] = 4
        fB[0] = 60
        fG[0] = 60
        fR[0] = 220
        fB[1] = 60
        fG[1] = 60
        fR[1] = 220
        fB[2] = 60
        fG[2] = 190
        fR[2] = 60
        fB[3] = 60
        fG[3] = 190
        fR[3] = 60
        fB[4] = 220
        fG[4] = 90
        fR[4] = 50
        fB[5] = 220
        fG[5] = 90
        fR[5] = 50
        fB[6] = 50
        fG[6] = 200
        fR[6] = 210
        fB[7] = 50
        fG[7] = 200
        fR[7] = 210
        fB[8] = 200
        fG[8] = 60
        fR[8] = 200
        fB[9] = 200
        fG[9] = 60
        fR[9] = 200
        fB[10] = 210
        fG[10] = 200
        fR[10] = 60
        fB[11] = 210
        fG[11] = 200
        fR[11] = 60
    }

    def transformAll {
        c1: Int = cos16(spinX)
        s1: Int = sin16(spinX)
        c2: Int = cos16(spinY)
        s2: Int = sin16(spinY)
        i: Int = 0
        while i < 8 {
            x0: Int = vx[i]
            y0: Int = vy[i]
            z0: Int = vz[i]
            y1: Int = (y0 * c1 - z0 * s1) / ONE
            z1: Int = (y0 * s1 + z0 * c1) / ONE
            x2: Int = (x0 * c2 + z1 * s2) / ONE
            z2: Int = (0 - x0 * s2 + z1 * c2) / ONE
            wx[i] = x2
            wy[i] = y1
            wz[i] = z2
            i = i + 1
        }
    }

    def projectAll {
        i: Int = 0
        while i < 8 {
            zt: Int = wz[i] + CAMZ
            px[i] = W / 2 + (wx[i] * FOCAL / zt) / ONE
            py[i] = H / 2 - (wy[i] * FOCAL / zt) / ONE
            pz[i] = zt
            i = i + 1
        }
    }

    def faceShade[ti: Int] -> Int {
        i0: Int = fv[ti * 3]
        i1: Int = fv[ti * 3 + 1]
        i2: Int = fv[ti * 3 + 2]
        a1: Int = wx[i1] - wx[i0]
        b1: Int = wy[i1] - wy[i0]
        c1: Int = wz[i1] - wz[i0]
        a2: Int = wx[i2] - wx[i0]
        b2: Int = wy[i2] - wy[i0]
        c2: Int = wz[i2] - wz[i0]
        nx: Int = (b1 * c2 - c1 * b2) / ONE
        ny: Int = (c1 * a2 - a1 * c2) / ONE
        nz: Int = (a1 * b2 - b1 * a2) / ONE
        d: Int = (nx * LX + ny * LY + nz * LZ) / ONE
        if d < 0 { d = 0 }
        if d > ONE { d = ONE }
        return ONE * 30 / 100 + d * 70 / 100
    }

    def drawTri[ti: Int] {
        i0: Int = fv[ti * 3]
        i1: Int = fv[ti * 3 + 1]
        i2: Int = fv[ti * 3 + 2]
        x0: Int = px[i0]
        y0: Int = py[i0]
        x1: Int = px[i1]
        y1: Int = py[i1]
        x2: Int = px[i2]
        y2: Int = py[i2]
        z0: Int = pz[i0]
        z1: Int = pz[i1]
        z2: Int = pz[i2]
        area: Int = (x1 - x0) * (y2 - y0) - (y1 - y0) * (x2 - x0)
        if area != 0 {
            if area < 0 {
                tx: Int = x1
                ty: Int = y1
                tz: Int = z1
                x1 = x2
                y1 = y2
                z1 = z2
                x2 = tx
                y2 = ty
                z2 = tz
                area = 0 - area
            }
            shade: Int = faceShade(ti)
            sb: Int = fB[ti] * shade / ONE
            sg: Int = fG[ti] * shade / ONE
            sr: Int = fR[ti] * shade / ONE
            xmin: Int = x0
            if x1 < xmin { xmin = x1 }
            if x2 < xmin { xmin = x2 }
            xmax: Int = x0
            if x1 > xmax { xmax = x1 }
            if x2 > xmax { xmax = x2 }
            ymin: Int = y0
            if y1 < ymin { ymin = y1 }
            if y2 < ymin { ymin = y2 }
            ymax: Int = y0
            if y1 > ymax { ymax = y1 }
            if y2 > ymax { ymax = y2 }
            if xmin < 0 { xmin = 0 }
            if ymin < y0b { ymin = y0b }
            if xmax > W - 1 { xmax = W - 1 }
            if ymax > y1b { ymax = y1b }
            y: Int = ymin
            while y <= ymax {
                x: Int = xmin
                while x <= xmax {
                    w0: Int = (x1 - x) * (y2 - y) - (y1 - y) * (x2 - x)
                    w1: Int = (x2 - x) * (y0 - y) - (y2 - y) * (x0 - x)
                    w2: Int = (x0 - x) * (y1 - y) - (y0 - y) * (x1 - x)
                    if w0 >= 0 and w1 >= 0 and w2 >= 0 {
                        znum: Int = z0 * w0 + z1 * w1 + z2 * w2
                        z: Int = znum / area
                        idx: Int = y * W + x
                        old: Int = load64(ptrAdd(zbP, idx * 8))
                        if z < old {
                            store64(ptrAdd(zbP, idx * 8), z)
                            pp: Ptr = ptrAdd(fbP, idx * 4)
                            store8(pp, sb)
                            store8(ptrAdd(pp, 1), sg)
                            store8(ptrAdd(pp, 2), sr)
                            store8(ptrAdd(pp, 3), 0)
                        }
                    }
                    x = x + 1
                }
                y = y + 1
            }
        }
    }

    def renderBand {
        y: Int = y0b
        while y <= y1b {
            x: Int = 0
            while x < W {
                o: Int = (y * W + x) * 4
                store8(ptrAdd(fbP, o), 30)
                store8(ptrAdd(fbP, o + 1), 26)
                store8(ptrAdd(fbP, o + 2), 22)
                store8(ptrAdd(fbP, o + 3), 0)
                store64(ptrAdd(zbP, (y * W + x) * 8), 4611686018427387903)
                x = x + 1
            }
            y = y + 1
        }
        transformAll()
        projectAll()
        t: Int = 0
        while t < 12 {
            drawTri(t)
            t = t + 1
        }
    }
"""

lines = []
lines.append("# cube3d_par.wk —— Whisker 3D 引擎·并行版（Actor 分片渲染，榨干 CPU）")
lines.append("#")
lines.append("# 架构：Main 协调 + 12 个 Band actor 各渲染 1/12 屏幕条带")
lines.append("# CPU 占用 ≈ (12+1)/24 = 50%（可调 BANDS）")
lines.append("# 运行：cube3d_par.exe（ESC 退出）")
lines.append("")
lines.append("actor Band {")
lines.append("    ONE: Int = 65536")
lines.append("    FOCAL: Int = 27525120")
lines.append("    CAMZ: Int = 262144")
lines.append("    LX: Int = -32768")
lines.append("    LY: Int = -45875")
lines.append("    LZ: Int = 32768")
lines.append("    W: Int = 480")
lines.append("    H: Int = 360")
lines.append("    BANDS: Int = 12")
lines.append("    fbP: Ptr")
lines.append("    zbP: Ptr")
lines.append("    my: Int = 0")
lines.append("    y0b: Int = 0")
lines.append("    y1b: Int = 0")
lines.append("    spinX: Int = 0")
lines.append("    spinY: Int = 0")
lines.append("    vx: Int[8]")
lines.append("    vy: Int[8]")
lines.append("    vz: Int[8]")
lines.append("    fv: Int[36]")
lines.append("    fB: Int[12]")
lines.append("    fG: Int[12]")
lines.append("    fR: Int[12]")
lines.append("    wx: Int[8]")
lines.append("    wy: Int[8]")
lines.append("    wz: Int[8]")
lines.append("    px: Int[8]")
lines.append("    py: Int[8]")
lines.append("    pz: Int[8]")
lines.append("")
lines.append("    on Reg[a: Int, b: Int, c: Int] {")
lines.append("        fbP = intToPtr(a)")
lines.append("        zbP = ptrAdd(intToPtr(b), 8 + BANDS * 8)")
lines.append("        my = c")
lines.append("        y0b = my * H / BANDS")
lines.append("        y1b = (my + 1) * H / BANDS - 1")
lines.append("        initCube()")
lines.append("    }")
lines.append("")
lines.append("    on Tick[t: Int] {")
lines.append("        if t == -1 { return }")
lines.append("        spinX = (t * 7) % 256")
lines.append("        spinY = (t * 11) % 256")
lines.append("        renderBand()")
lines.append("        store64(flg, t)")
lines.append("    }")
lines.append("")
lines.append(band_engine)
lines.append("}")
lines.append("")
# Main actor
lines.append("actor Main {")
lines.append("    W: Int = 480")
lines.append("    H: Int = 360")
lines.append("    fb: Ptr")
lines.append("    zb: Ptr")
for i in range(NB):
    lines.append(f"    b{i}: ActorRef[Band]")
lines.append("    on Start {")
lines.append("        fb = alloc(W * H * 4)")
lines.append("        zb = alloc(8 + NB * 8 + W * H * 8)".replace("NB", str(NB)))
lines.append("        fbI: Int = ptrToInt(fb)")
lines.append("        zbI: Int = ptrToInt(zb)")
for i in range(NB):
    lines.append(f"        b{i} = spawn Band")
    lines.append(f"        b{i}.send(Reg(fbI, zbI, {i}))")
lines.append("        r: Int = winOpen(\"Whisker 3D Parallel\", W, H)")
lines.append("        if r == 0 { print(\"fail\"); return }")
lines.append("        live: Int = 1")
lines.append("        frame: Int = 0")
lines.append("        while live == 1 {")
for i in range(NB):
    lines.append(f"            b{i}.send(Tick(frame + 1))")
lines.append("            # 等全部完成（轮询标志位）")
lines.append("            alldone: Int = 0")
lines.append("            while alldone == 0 {")
lines.append("                alldone = 1")
lines.append("                i: Int = 0")
lines.append("                while i < BANDS {".replace("BANDS", str(NB)))
lines.append("                    if load64(ptrAdd(zb, 8 + i * 8)) != frame + 1 { alldone = 0 }")
lines.append("                    i = i + 1")
lines.append("                }")
lines.append("            }")
lines.append("            winPresent(fb, W, H)")
lines.append("            if winPump() == 0 { live = 0 }")
lines.append("            if keyAsync(27) != 0 { live = 0 }")
lines.append("            frame = frame + 1")
lines.append("            if frame % 300 == 0 { print(\"frame \", frame) }")
lines.append("        }")
lines.append("        winClose()")
lines.append("        print(\"并行渲染结束 \", frame)")
lines.append("    }")
lines.append("}")
open(r"demos/3d/cube3d_par.wk", "w", encoding="utf-8").write("\n".join(lines))
print(f"cube3d_par.wk 生成完成（{NB} Band）")
