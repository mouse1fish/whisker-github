p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
old = '''            zt: Int = wz[i] + CAMZ             # 相机前移
            px[i] = W / 2 + (wx[i] * FOCAL / zt) / ONE
            py[i] = H / 2 - (wy[i] * FOCAL / zt) / ONE'''
new = '''            zt: Int = wz[i] + CAMZ             # 相机前移（16.16）
            # 屏幕偏移 = (世界坐标(16.16) * 焦距(像素)) / 深度(16.16) -> 直接得像素
            px[i] = W / 2 + (wx[i] * FOCAL) / zt
            py[i] = H / 2 - (wy[i] * FOCAL) / zt'''
assert old in s, "投影"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("投影修正 OK")
