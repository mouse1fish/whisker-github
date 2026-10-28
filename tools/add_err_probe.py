# -*- coding: utf-8 -*-
"""err 打印加 pi 定位。"""
p = r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk"
s = open(p, encoding="utf-8").read()
old = 'def err[msg: Str] { print("[wkcc] ", msg, "（附近：", pt(0), "）"); tAdvance() }'
new = 'def err[msg: Str] { print("[wkcc] pi=", intToStr(pi), " ", msg, "（附近：", pt(0), "）"); tAdvance() }'
assert old in s, "err anchor not found"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("err probe added")
