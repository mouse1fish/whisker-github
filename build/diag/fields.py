import re
src = open(r"tools/wkcc.wk", encoding="utf-8").read().splitlines()
# 抓 actor Main { 之后、第一个 def 之前的字段声明行
fields = []
in_main = False
for ln in src:
    if re.match(r"\s*actor Main\s*\{", ln):
        in_main = True; continue
    if in_main and re.match(r"\s*def ", ln):
        break
    m = re.match(r"\s+(\w+):\s*([A-Za-z]+)(\[(\d+)\])?", ln)
    if in_main and m:
        fields.append((m.group(1), m.group(2), int(m.group(4)) if m.group(4) else 0))
print(f"字段总数: {len(fields)}")
off = 48
for name, ty, n in fields:
    size = n * 8 if n else 8
    print(f"  {off:#08x}  {name}: {ty}{'['+str(n)+']' if n else ''}  (+{size})")
    off += size
print(f"总大小 = {off:#x} ({off})")
