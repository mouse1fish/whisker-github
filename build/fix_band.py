p = r"demos/3d/cube3d_par.wk"
s = open(p, encoding="utf-8").read()
old = '''    last: Int = 0
    live: Int = 1'''
new = '''    last: Int = 0
    live: Int = 1
    spinX: Int = 0
    spinY: Int = 0'''
assert old in s, "Band 字段"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("Band 字段补齐 OK")
