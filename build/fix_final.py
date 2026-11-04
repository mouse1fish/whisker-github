p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
# 1) 窗口标题改 ASCII（CreateWindowExA 是 ANSI 接口，中文需宽字符版；此处从简）
s = s.replace('r: Int = winOpen("Whisker 3D —— 定点软件光栅化", W, H)',
              'r: Int = winOpen("Whisker 3D - Fixed-Point Software Rasterizer", W, H)')
# 2) FPS 公式修正（每 30 帧重置计时窗口）
old = '''            frames = frames + 1
            if frames % 30 == 0 {
                dt: Int = wallMs() - t0
                if dt > 0 { print("FPS ≈ ", 30000 / dt) }
            }'''
new = '''            frames = frames + 1
            if frames % 30 == 0 {
                dt: Int = wallMs() - t0
                if dt > 0 { print("FPS = ", 30000 / dt) }
                t0 = wallMs()
            }'''
assert old in s, "FPS 公式"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("标题 + FPS 修正 OK")
