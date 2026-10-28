# -*- coding: utf-8 -*-
"""显示任意 run_pe_test 输出文件。用法: python tools/show_file.py <path>"""
import sys, ast

raw = open(sys.argv[1], "rb").read()
try:
    txt = raw.decode("utf-8")
except Exception:
    txt = raw.decode("utf-16", errors="replace")

i = txt.find("stdout = b'")
if i < 0:
    print("(无 stdout)")
    print(txt[:300])
    sys.exit()
rest = txt[i + 11:]
# stdout 值以 b'...' 结束，后面是 \nexit = ...
j = rest.rfind("'\nexit")
if j < 0:
    j = len(rest)
body = rest[:j]
data = ast.literal_eval("b'" + body + "'")
s = data.decode("utf-8", errors="replace")
for l in s.splitlines():
    print(l[:160])
print("---")
for l in txt.splitlines():
    if l.startswith("exit"):
        print(l)
