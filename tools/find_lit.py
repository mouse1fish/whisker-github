# -*- coding: utf-8 -*-
"""找 wkcc.wk 里 ptrAdd/src/pos 的字符串字面量使用处。"""
s = open(r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk", encoding="utf-8").read()
lines = s.splitlines()
for i, l in enumerate(lines):
    if '"ptrAdd"' in l or '"src"' in l or '"pos"' in l:
        print(f"{i+1}: {l.strip()[:90]}")
