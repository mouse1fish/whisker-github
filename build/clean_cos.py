import re
# 1) cos16 内联（去掉未回填的 jmp）
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
old = '''    a.label("rt_cos16")
    a.add_ri(RCX, 64)
    a.jmp("rt_sin16")

    a.label("rt_sin16")'''
new = '''    a.label("rt_cos16")                     # 与 sin16 同体（角度 +64），避免跨标签跳转
    a.add_ri(RCX, 64)

    a.label("rt_sin16")'''
assert old in s, "cos16"; s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("cos16 内联 OK")

# 2) 清 runHeadless 的调试打印
p2 = r"demos/3d/cube3d.wk"
s2 = open(p2, encoding="utf-8").read()
m = re.search(r"    def runHeadless\[n: Int\] \{[\s\S]*?        i: Int = 0", s2)
assert m, "runHeadless"
s2 = s2[:m.start()] + "    def runHeadless[n: Int] {\n        i: Int = 0" + s2[m.end():]
open(p2, "w", encoding="utf-8").write(s2)
print("打点清理 OK")
