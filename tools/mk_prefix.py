# -*- coding: utf-8 -*-
"""取 wkcc.wk 前 N 行写入 lex_input.txt。用法: python tools/mk_prefix.py N"""
import sys

p = r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk"
lines = open(p, encoding="utf-8").read().splitlines(keepends=True)
n = int(sys.argv[1])
out = r"H:\trea-xiancheng-bianyiqi\build\lex_input.txt"
open(out, "w", encoding="utf-8").write("".join(lines[:n]) + "\nactor Main { on Start { print(1) } }\n")
print(f"lex_input.txt <- wkcc.wk 前 {n} 行 + 最小 actor 包裹")
