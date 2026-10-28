# -*- coding: utf-8 -*-
"""统计 wkcc.wk 的 def 数量、token 估算、字符串容量压力。"""
import re

s = open(r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk", encoding="utf-8").read()
defs = re.findall(r"^\s*def (\w+)", s, re.M)
print("def 数量:", len(defs), "（fnName 容量 64）")
print("源码字节数:", len(s.encode("utf-8")))
strs = re.findall(r'"[^"\n]*"', s)
total = sum(len(x) - 2 for x in strs)
print("字符串字面量:", len(strs), "（rbuf 压力总字节:", total, "）")
# 粗略 token 估算：标识符+数字+标点+换行
idents = re.findall(r"[A-Za-z_][A-Za-z0-9_]*", s)
puncs = re.findall(r"[{}()\[\]:;,.\-+*/<>=!]", s)
nls = s.count("\n")
print("token 估算: idents", len(idents), "+ puncs", len(puncs), "+ nl", nls,
      "=", len(idents) + len(puncs) + nls, "（tkKind 容量 65536）")
