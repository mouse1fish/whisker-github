p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
old = '''            zt: Int = wz[i] + CAMZ             # 相机前移（16.16）
            # 屏幕偏移 = (世界坐标(16.16) * 焦距(像素)) / 深度(16.16) -> 直接得像素
            px[i] = W / 2 + (wx[i] * FOCAL) / zt
            py[i] = H / 2 - (wy[i] * FOCAL) / zt'''
new = '''            zt: Int = wz[i] + CAMZ             # 相机前移（16.16）
            # 屏幕偏移 = ((世界坐标(16.16) * 焦距(16.16)) / 深度(16.16)) / ONE -> 像素
            px[i] = W / 2 + (wx[i] * FOCAL / zt) / ONE
            py[i] = H / 2 - (wy[i] * FOCAL / zt) / ONE'''
assert old in s, "投影回退"
s = s.replace(old, new)
# 调试打点：无头模式先打印 8 顶点投影
old2 = '''    def runHeadless[n: Int] {
        i: Int = 0'''
new2 = '''    def runHeadless[n: Int] {
        # 调试：打印第 0 帧的投影顶点
        spinX = 0
        spinY = 0
        transformAll()
        projectAll()
        d: Int = 0
        while d < 8 {
            print("v", d, ": (", px[d], ",", py[d], ") z=", pz[d])
            d = d + 1
        }
        i: Int = 0'''
assert old2 in s, "runHeadless"
s = s.replace(old2, new2)
open(p, "w", encoding="utf-8").write(s)
print("回退 + 打点 OK")
