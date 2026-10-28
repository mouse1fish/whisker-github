# -*- coding: utf-8 -*-
"""把字段布局打印移到 resolveFnFx 之后（parse 完成后 fldCount 才有值）。"""
p = r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk"
s = open(p, encoding="utf-8").read()

old = (
    "        resolveFx()\n"
    "        resolveFnFx()\n"
    '        print("[dbg7] resolveFx ok, nfix=", intToStr(fxCount))'
)
new = (
    "        resolveFx()\n"
    "        resolveFnFx()\n"
    '        print("[dbg7] resolveFx ok, nfix=", intToStr(fxCount))\n'
    "        i2: Int = 0\n"
    "        while i2 < fldCount {\n"
    '            print("[fld] ", fldName[i2], " ", intToStr(fldOff[i2]))\n'
    "            i2 = i2 + 1\n"
    "        }"
)
assert old in s, "anchor not found"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("probe moved after resolveFx")
