# -*- coding: utf-8 -*-
"""parseUnary 支持括号分组表达式。"""
p = r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk"
s = open(p, encoding="utf-8").read()
old = (
    "    def parseUnary {\n"
    '        if tIsPunc("-") { tAdvance(); parseUnary(); e8(72); e8(247); e8(216); return }  # neg rax'
)
new = (
    "    def parseUnary {\n"
    "        if tIsPunc(\"(\") {\n"
    "            tAdvance()\n"
    "            parseExpr()\n"
    "            tExpect(\")\")\n"
    "            return\n"
    "        }\n"
    '        if tIsPunc("-") { tAdvance(); parseUnary(); e8(72); e8(247); e8(216); return }  # neg rax'
)
assert old in s, "parseUnary anchor not found"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("paren grouping added")
