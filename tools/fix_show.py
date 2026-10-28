# -*- coding: utf-8 -*-
"""show_out 加 [ctx] 过滤。"""
p = r"H:\trea-xiancheng-bianyiqi\tools\show_out.py"
s = open(p, encoding="utf-8").read()
old = 'if "[wkcc]" in l or "dbg" in l or "fldcount" in l or "selfhost" in l:'
new = 'if "[wkcc]" in l or "[ctx]" in l or "dbg" in l or "fldcount" in l or "selfhost" in l:'
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("ok")
