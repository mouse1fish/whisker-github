import re
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
# 删掉旧的 print_float 部分（从 rt_print_float 到 rt_pf_zero 的 f.close()）
m = re.search(r'    a\.note\("rt_print_float（rcx=Float bits -> 打印 N\.NNNNNN）"\)[\s\S]*?a\.label\("rt_pf_zero"\)\n    f\.close\(\)\n', s)
assert m, "print_float 块"
s = s[:m.start()] + s[m.end():]
open(p, "w", encoding="utf-8").write(s)
print("简化 print OK")
