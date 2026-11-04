import re
p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
# 删掉被拼接成一行的颜色块
s = re.sub(r"\n *\# 面底色（B, G, R）内联[^\n]*", "", s)
cols = [(60,60,220),(60,60,220),(60,190,60),(60,190,60),(220,90,50),(220,90,50),
        (50,200,210),(50,200,210),(200,60,200),(200,60,200),(210,200,60),(210,200,60)]
lines = ["        # 面底色（B, G, R）内联"]
for i,(b,g,r) in enumerate(cols):
    lines.append(f"        fB[{i}] = {b}")
    lines.append(f"        fG[{i}] = {g}")
    lines.append(f"        fR[{i}] = {r}")
block = "\n".join(lines)
# 插到 fv[35] = 4 之后
old = "        fv[35] = 4\n"
assert old in s, "fv35 锚点"
s = s.replace(old, old + block + "\n", 1)
open(p, "w", encoding="utf-8").write(s)
print("颜色块重写 OK（多行）")
# 校验
import subprocess
r = subprocess.run(["python","-c","import re;s=open(r'demos/3d/cube3d.wk',encoding='utf-8').read();print('fB 行数:', len(re.findall(r'fB\\[\\d+\\] =', s)))"], capture_output=True, text=True)
print(r.stdout.strip(), r.stderr.strip())
