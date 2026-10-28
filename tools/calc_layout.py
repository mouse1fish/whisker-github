# -*- coding: utf-8 -*-
"""模拟 wkcc.wk parseField 的字段偏移累加，打印每个字段的 fldOff。"""
import re

s = open(r"H:\trea-xiancheng-bianyiqi\tools\wkcc.wk", encoding="utf-8").read()

# 只取 actor Main 的顶层字段声明（4 空格缩进 `名: 类型`，行内无 def）
fields = []
for m in re.finditer(r"^    (\w+): ([^\n=]+?)(?:\s*=.*)?$", s, re.M):
    name, ty = m.group(1), m.group(2).strip()
    if name in ("def",):  # 防 def 行误配
        continue
    arrn = 0
    m2 = re.search(r"\[(\d+)\]", ty)
    if m2:
        arrn = int(m2.group(1))
    fields.append((name, ty.split("[")[0], arrn))

act_size = 48
print(f"{'字段':<16} {'类型':<14} {'arrN':>7} {'fldOff':>10} {'大小':>9}")
for name, ty, arrn in fields:
    off = act_size
    sz = 8 * arrn if arrn > 0 else 8
    act_size += sz
    mark = ""
    if off <= 1122912 < off + sz:
        mark = "   <<< 包含 0x112A60"
    if arrn > 0 or off <= 1122912 <= off + 2048:
        print(f"{name:<16} {ty:<14} {arrn:>7} {off:>10} {sz:>9}{mark}")
print(f"\nactor 总大小 = {act_size}")
