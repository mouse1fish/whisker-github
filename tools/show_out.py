# -*- coding: utf-8 -*-
"""显示 boot_out.txt 里 stdout 的 [wkcc]/dbg 行（literal_eval 精确还原）。"""
import ast

raw = open(r"H:\trea-xiancheng-bianyiqi\build\boot_out.txt", "rb").read()
try:
    txt = raw.decode("utf-8")
except Exception:
    txt = raw.decode("utf-16", errors="replace")

i = txt.find("stdout = b'")
j = txt.rfind("'\nexit")
if j < 0:
    j = txt.rfind("'")
body = txt[i + 11:j]
data = ast.literal_eval("b'" + body + "'")
s = data.decode("utf-8", errors="replace")
for l in s.splitlines():
    if "[wkcc]" in l or "[ctx]" in l or "dbg" in l or "fldcount" in l or "selfhost" in l:
        print(l[:150])
