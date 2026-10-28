# -*- coding: utf-8 -*-
"""加 fldcount 运行时打印。"""
p = r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk"
s = open(p, encoding="utf-8").read()

old = (
    "        i2: Int = 0\n"
    "        while i2 < fldCount {\n"
    '            print("[fld] ", fldName[i2], " ", intToStr(fldOff[i2]))\n'
    "            i2 = i2 + 1\n"
    "        }"
)
new = (
    '        print("[fldcount] ", intToStr(fldCount), " fxCount=", intToStr(fxCount), " count=", intToStr(count))\n'
    "        i2: Int = 0\n"
    "        while i2 < fldCount {\n"
    '            print("[fld] ", fldName[i2], " ", intToStr(fldOff[i2]))\n'
    "            i2 = i2 + 1\n"
    "        }"
)
assert old in s, "anchor not found"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("fldcount probe added")
