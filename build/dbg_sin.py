p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
old = '''        # 调试：数组内容 + 投影顶点
        print("raw vx: ", vx[0], " ", vx[1], " ", vx[4])'''
new = '''        # 调试：定点三角函数
        print("sin16(0)=", sin16(0), " sin16(64)=", sin16(64), " cos16(0)=", cos16(0), " sin16(128)=", sin16(128))
        # 调试：数组内容 + 投影顶点
        print("raw vx: ", vx[0], " ", vx[1], " ", vx[4])'''
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
