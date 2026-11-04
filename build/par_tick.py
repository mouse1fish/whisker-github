p = r"demos/3d/cube3d_par.wk"
s = open(p, encoding="utf-8").read()
# Band 的 on Reg：去掉 forever loop，改为单次渲染 + 完成标志
old = '''        initCube()
        # 常驻循环：等票 → 渲染条带 → 标记完成
        while live == 1 {
            t: Int = load64(tkt)
            if t == 0 {
                sleepMs(1)           # 尚未开票：让核
            } elif t == 0 - 1 {
                live = 0             # 退出信号
            } elif t > last {
                spinX = (t * 7) % 256
                spinY = (t * 11) % 256
                renderBand()
                store64(flg, t)
                last = t
            }
        }
    }'''
new = '''        initCube()
    }

    on Tick[t: Int] {
        if t == 0 - 1 { return }
        spinX = (t * 7) % 256
        spinY = (t * 11) % 256
        renderBand()
        store64(flg, t)
    }'''
assert old in s, "Band Reg"; s = s.replace(old, new)
# Main: 改用 Tick 消息逐帧驱动
old2 = '''        # 票箱起步
        store64(zb, 1)
        live = 1
        while live == 1 {
            # 清完成标志（BANDS 个槽 @ zb + 8*idx）
            i = 0
            while i < BANDS {
                store64(ptrAdd(zb, 8 + i * 8), 0)
                i = i + 1
            }
            # 发票（写票箱 = 开工信号；x86 TSO 保证先清标志后见票）
            store64(zb, frame + 1)
            # 等全部完成（自旋轮询）
            alldone: Int = 0
            while alldone == 0 {
                alldone = 1
                i = 0
                while i < BANDS {
                    if load64(ptrAdd(zb, 8 + i * 8)) != frame + 1 {
                        alldone = 0
                    }
                    i = i + 1
                }
            }
            # 呈现
            winPresent(fb, W, H)
            if winPump() == 0 { live = 0 }
            if keyAsync(27) != 0 { live = 0 }
            frame = frame + 1
            if frame % 300 == 0 {
                print("frame ", frame)
            }
        }
        # 退出信号：票 = -1（各 Band 自行收尾退出）
        store64(zb, 0 - 1)
        sleepMs(300)
        winClose()
        print("并行渲染结束，共 ", frame, " 帧")'''
new2 = '''        # 逐帧驱动：每帧发 Tick 给所有 Band，等全部完成后 present
        live = 1
        while live == 1 {
            i = 0
            while i < BANDS {
                b2: ActorRef[Band] = bands[i]
                b2.send(Tick(frame + 1))
                i = i + 1
            }
            # 等全部 Band 完成（自旋读标志）
            alldone: Int = 0
            while alldone == 0 {
                alldone = 1
                i = 0
                while i < BANDS {
                    if load64(ptrAdd(zb, 8 + i * 8)) != frame + 1 {
                        alldone = 0
                    }
                    i = i + 1
                }
            }
            winPresent(fb, W, H)
            if winPump() == 0 { live = 0 }
            if keyAsync(27) != 0 { live = 0 }
            frame = frame + 1
            if frame % 300 == 0 { print("frame ", frame) }
        }
        winClose()
        print("并行渲染结束，共 ", frame, " 帧")'''
assert old2 in s, "Main 循环"; s = s.replace(old2, new2)
# 3) spawn 循环改为存 refs 数组 + 发 Reg
old3 = '''        i: Int = BANDS - 1
        while i >= 0 {
            b: ActorRef[Band] = spawn Band
            b.send(Reg(fbI, zbI, i))
            i = i - 1
        }'''
new3 = '''        i: Int = 0
        while i < BANDS {
            bands[i] = spawn Band
            bands[i].send(Reg(fbI, zbI, i))
            i = i + 1
        }'''
assert old3 in s, "spawn 循环"; s = s.replace(old3, new3)
# 4) 加 bands 数组字段
old4 = '''    fbI: Int = 0
    zbI: Int = 0
    frame: Int = 0
    live: Int = 1'''
new4 = '''    fbI: Int = 0
    zbI: Int = 0
    frame: Int = 0
    live: Int = 1
    bands: ActorRef[Band][24]'''
assert old4 in s, "bands 字段"; s = s.replace(old4, new4)
open(p, "w", encoding="utf-8").write(s)
print("Tick 模式重构完成")
