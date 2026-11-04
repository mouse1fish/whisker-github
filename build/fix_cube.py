p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()

# 1) 负数字段初值：一元负号
s = s.replace("    LX: Int = 0 - 32768", "    LX: Int = -32768")
s = s.replace("    LY: Int = 0 - 45875", "    LY: Int = -45875")

# 2) setTri/paintFace 4 参超限 -> 内联（删 def，直写字段）
old = '''            # 六个面（各 2 三角形）：前 后 左 右 上 下
        setTri(0, 4, 5, 6)
        setTri(1, 4, 6, 7)
        setTri(2, 1, 0, 3)
        setTri(3, 1, 3, 2)
        setTri(4, 0, 4, 7)
        setTri(5, 0, 7, 3)
        setTri(6, 5, 1, 2)
        setTri(7, 5, 2, 6)
        setTri(8, 7, 6, 2)
        setTri(9, 7, 2, 3)
        setTri(10, 0, 1, 5)
        setTri(11, 0, 5, 4)'''
new = '''            # 六个面（各 2 三角形）：前 后 左 右 上 下（索引表内联）
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
        fv[35] = 4'''
if old in s:
    s = s.replace(old, new)
    print("fv 内联 OK")
else:
    # 原文件缩进可能是 8 空格，尝试宽松匹配
    import re
    pat = re.compile(r"\n\s*# 六个面（各 2 三角形）[\s\S]*?setTri\(11, 0, 5, 4\)")
    assert pat.search(s), "未找到 setTri 块"
    s = pat.sub("\n" + new, s)
    print("fv 内联 OK（regex）")

import re
old2 = re.compile(r"\n\s*# 面底色（B, G, R）[\s\S]*?paintFace\(11, 210, 200, 60\)")
assert old2.search(s), "未找到 paintFace 块"
cols = [(60,60,220),(60,60,220),(60,190,60),(60,190,60),(220,90,50),(220,90,50),
        (50,200,210),(50,200,210),(200,60,200),(200,60,200),(210,200,60),(210,200,60)]
lines = ["\n        # 面底色（B, G, R）内联"]
for i,(b,g,r) in enumerate(cols):
    lines.append(f"        fB[{i}] = {b}")
    lines.append(f"        fG[{i}] = {g}")
    lines.append(f"        fR[{i}] = {r}")
s = old2.sub("".join(lines), s)
print("paintFace 内联 OK")

# 3) 删掉两个超限 def
for name in ("setTri", "paintFace"):
    pat = re.compile(rf"\n    def {name}\[[^\]]*\] \{{[\s\S]*?\n    \}}\n")
    s2 = pat.sub("\n", s)
    assert s2 != s, f"{name} def 未删除"
    s = s2
print("超限 def 已删")
open(p, "w", encoding="utf-8").write(s)
