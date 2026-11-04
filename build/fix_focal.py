p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
s = s.replace("    FOCAL: Int = 45875200          # 焦距 = 700 * 65536（字段初值须为字面量）",
              "    FOCAL: Int = 27525120          # 焦距 = 420 * 65536（字段初值须为字面量）")
# 清掉调试打点
import re
m = re.search(r"    def runHeadless\[n: Int\] \{[\s\S]*?        i: Int = 0", s)
assert m, "runHeadless"
s = s[:m.start()] + '''    def runHeadless[n: Int] {
        i: Int = 0''' + s[m.end():]
open(p, "w", encoding="utf-8").write(s)
print("取景微调 + 清打点 OK")
