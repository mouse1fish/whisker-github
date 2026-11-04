p = r"demos/3d/cube3d_par.wk"
s = open(p, encoding="utf-8").read()
# Band 需要一个 flg: Ptr 字段（在 on Reg 里设置，在 on Tick 里写完成标志）
s = s.replace("    spinY: Int = 0\n    vx: Int[8]",
              "    spinY: Int = 0\n    flg: Ptr\n    vx: Int[8]")
s = s.replace('''        zbP = ptrAdd(intToPtr(b), 8 + BANDS * 8)
        my = c''',
              '''        zbP = ptrAdd(intToPtr(b), 8 + BANDS * 8)
        flg = ptrAdd(intToPtr(b), 8 + c * 8)
        my = c''')
open(p, "w", encoding="utf-8").write(s)
print("flg 字段 OK")
