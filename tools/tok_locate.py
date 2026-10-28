# -*- coding: utf-8 -*-
"""用 Python 模拟词法（简化版）定位 token 1386 的源码位置。"""
import re

s = open(r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk", encoding="utf-8").read()
target = 1386

# 简易词法：与 wkcc.wk 的词法器近似（标识符/数字/字符串/注释/标点/换行）
toks = []
i = 0
n = len(s)
kw_pat = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
line_starts = [0] + [m.end() for m in re.finditer(r"\n", s)]

def lineno(pos):
    import bisect
    return bisect.bisect_right(line_starts, pos)

while i < n and len(toks) <= target + 2:
    c = s[i]
    if c in " \t\r":
        i += 1; continue
    if s.startswith("//", i):
        j = s.find("\n", i); i = j if j >= 0 else n; continue
    if s.startswith("/*", i):
        j = s.find("*/", i); i = j + 2 if j >= 0 else n; continue
    if c == "\n":
        toks.append((i, "NL", "\\n")); i += 1; continue
    if c == '"':
        j = i + 1
        while j < n and s[j] != '"':
            j += 2 if s[j] == "\\" else 1
        toks.append((i, "STR", s[i:j+1])); i = j + 1; continue
    m = kw_pat.match(s, i)
    if m:
        toks.append((i, "ID", m.group())); i = m.end(); continue
    if c.isdigit():
        m2 = re.match(r"[0-9][0-9a-fA-FxX_]*", s[i:])
        toks.append((i, "NUM", m2.group())); i += m2.end(); continue
    # 多字符标点
    for p in ("..=", "..", "->", "&&", "||", "==", "!=", "<=", ">="):
        if s.startswith(p, i):
            toks.append((i, "PUNC", p)); i += len(p); break
    else:
        toks.append((i, "PUNC", c)); i += 1

# 忽略 NL 的计数方式未知，打印 target 前后（含/不含 NL 两种）
print("=== 含 NL 的 token", target, "===")
for k in range(max(0, target - 4), min(len(toks), target + 4)):
    pos, kind, v = toks[k]
    print(f"tok[{k}] line={lineno(pos)}: {kind} {v[:40]!r}")
print()
print("=== 源码 1386 附近 ===")
for k in range(max(0, target - 6), min(len(toks), target + 3)):
    pos, kind, v = toks[k]
    ln = lineno(pos)
    print(f"tok[{k}] line={ln}: {s[line_starts[ln-1]:line_starts[ln]].rstrip()[:90]!r}")
