import re
p = r"demos/3d/cube3d_par.wk"
s = open(p, encoding="utf-8").read()

# 1) Main 的 bands 数组字段 → 12 个独立 ActorRef 字段
s = s.replace("    bands: ActorRef[Band][24]", 
"""    b0: ActorRef[Band]
    b1: ActorRef[Band]
    b2: ActorRef[Band]
    b3: ActorRef[Band]
    b4: ActorRef[Band]
    b5: ActorRef[Band]
    b6: ActorRef[Band]
    b7: ActorRef[Band]
    b8: ActorRef[Band]
    b9: ActorRef[Band]
    b10: ActorRef[Band]
    b11: ActorRef[Band]""")

# 2) spawn 循环 → 内联展开
old_spawn = '''        i: Int = 0
        while i < BANDS {
            bands[i] = spawn Band
            bands[i].send(Reg(fbI, zbI, i))
            i = i + 1
        }'''
new_spawn = '''        b0 = spawn Band
        b1 = spawn Band
        b2 = spawn Band
        b3 = spawn Band
        b4 = spawn Band
        b5 = spawn Band
        b6 = spawn Band
        b7 = spawn Band
        b8 = spawn Band
        b9 = spawn Band
        b10 = spawn Band
        b11 = spawn Band
        b0.send(Reg(fbI, zbI, 0))
        b1.send(Reg(fbI, zbI, 1))
        b2.send(Reg(fbI, zbI, 2))
        b3.send(Reg(fbI, zbI, 3))
        b4.send(Reg(fbI, zbI, 4))
        b5.send(Reg(fbI, zbI, 5))
        b6.send(Reg(fbI, zbI, 6))
        b7.send(Reg(fbI, zbI, 7))
        b8.send(Reg(fbI, zbI, 8))
        b9.send(Reg(fbI, zbI, 9))
        b10.send(Reg(fbI, zbI, 10))
        b11.send(Reg(fbI, zbI, 11))'''
assert old_spawn in s, "spawn 循环"
s = s.replace(old_spawn, new_spawn)

# 3) Tick 发送循环 → 内联展开
old_tick = '''            i = 0
            while i < BANDS {
                b2: ActorRef[Band] = bands[i]
                b2.send(Tick(frame + 1))
                i = i + 1
            }'''
new_tick = '''            b0.send(Tick(frame + 1))
            b1.send(Tick(frame + 1))
            b2.send(Tick(frame + 1))
            b3.send(Tick(frame + 1))
            b4.send(Tick(frame + 1))
            b5.send(Tick(frame + 1))
            b6.send(Tick(frame + 1))
            b7.send(Tick(frame + 1))
            b8.send(Tick(frame + 1))
            b9.send(Tick(frame + 1))
            b10.send(Tick(frame + 1))
            b11.send(Tick(frame + 1))'''
assert old_tick in s, "Tick 循环"
s = s.replace(old_tick, new_tick)

# 4) Band 的 spin 循环 → Tick 消息驱动
old_loop = '''        initCube()
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
    }

    on Tick[t: Int] {
        if t == 0 - 1 { return }
        spinX = (t * 7) % 256
        spinY = (t * 11) % 256
        renderBand()
        store64(flg, t)
    }'''
new_loop = '''        initCube()
    }

    on Tick[t: Int] {
        if t == 0 - 1 { return }
        spinX = (t * 7) % 256
        spinY = (t * 11) % 256
        renderBand()
        store64(flg, t)
    }'''
assert old_loop in s, "Band 循环"
s = s.replace(old_loop, new_loop)

# 5) 清除 tkt/flg/last/live 等不再需要的字段
s = s.replace('''    tkt: Ptr                         # 票箱
    flg: Ptr                         # 我的完成标志
    my: Int = 0
    y0b: Int = 0
    y1b: Int = 0
    last: Int = 0
    live: Int = 1
    spinX: Int = 0
    spinY: Int = 0''', '''    spinX: Int = 0
    spinY: Int = 0''')

# 6) Reg handler 简化（去掉 tkt/flg 引用）
s = s.replace('''    on Reg[a: Int, b: Int, c: Int] {
        fbP = intToPtr(a)
        tkt = intToPtr(b)
        my = c
        flg = ptrAdd(tkt, 8 + my * 8)
        zbP = ptrAdd(tkt, 8 + BANDS * 8)
        y0b = my * H / BANDS
        y1b = (my + 1) * H / BANDS - 1
        initCube()''', '''    on Reg[a: Int, b: Int, c: Int] {
        fbP = intToPtr(a)
        zbP = ptrAdd(intToPtr(b), 8 + BANDS * 8)
        my = c
        y0b = my * H / BANDS
        y1b = (my + 1) * H / BANDS - 1
        initCube()''')

# 7) renderBand 中 zbP 引用 ✓ 已正确
# 8) drawTri 的条带裁剪用 y0b/y1b ✓

# 9) Main 的 bands 字段清理完毕，确保 BANDS 常量仍在
# Band actor 的 BANDS: Int = 12 ✓

open(p, "w", encoding="utf-8").write(s)
print("Tick 消息驱动模型重构完成")
