p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
old = '''        # 调试：打印第 0 帧的投影顶点
        spinX = 0
        spinY = 0
        transformAll()
        projectAll()
        d: Int = 0
        while d < 8 {
            print("v", d, ": (", px[d], ",", py[d], ") z=", pz[d])
            d = d + 1
        }'''
new = '''        # 调试：数组内容 + 投影顶点
        print("raw vx: ", vx[0], " ", vx[1], " ", vx[4])
        print("raw fv: ", fv[0], " ", fv[1], " ", fv[2])
        spinX = 0
        spinY = 0
        transformAll()
        print("after tf wx: ", wx[0], " ", wx[1])
        projectAll()
        d: Int = 0
        while d < 8 {
            print("v", d, ": (", px[d], ",", py[d], ") z=", pz[d])
            d = d + 1
        }'''
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("数组打点 OK")
