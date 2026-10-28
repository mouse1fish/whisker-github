# -*- coding: utf-8 -*-
"""err 打印加 token 上下文。"""
p = r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk"
s = open(p, encoding="utf-8").read()
old = 'def err[msg: Str] { print("[wkcc] pi=", intToStr(pi), " ", msg, "（附近：", pt(0), "）"); tAdvance() }'
new = (
    'def err[msg: Str] {\n'
    '        print("[wkcc] pi=", intToStr(pi), " ", msg, "（附近：", pt(0), "）")\n'
    '        print("[ctx] ", pt(-4), " | ", pt(-3), " | ", pt(-2), " | ", pt(-1), " | ", pt(0), " | ", pt(1))\n'
    "        tAdvance()\n"
    "    }"
)
assert old in s, "err anchor not found"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("err ctx added")
