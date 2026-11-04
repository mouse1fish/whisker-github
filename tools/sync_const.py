"""从 build/const_block.txt（extract_runtime.py 输出）同步常量到 tools/wkcc.wk"""
import re
import sys

blk = None
for enc in ("utf-8-sig", "utf-16", "utf-8", "gbk"):
    try:
        blk = open(r"build/const_block.txt", encoding=enc).read()
        break
    except (UnicodeDecodeError, UnicodeError):
        continue
if blk is None:
    print("!! 无法解码 const_block.txt")
    sys.exit(1)
keys = ("OFF_\\w+|RT_TEXT_LEN|RT_RDATA_LEN|RT_DATA_LEN|RT_DATA_OFF|IAT_RVA|IAT_IN_DATA")
vals = dict(re.findall(rf"^\s+({keys}):\s*Int\s*=\s*(\d+)", blk, re.M))
if not vals:
    print("!! const_block.txt 里没找到常量，检查 extract 输出")
    sys.exit(1)

p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
changed = []
for k, v in vals.items():
    pat = re.compile(rf"^(\s*{k}:\s*Int\s*=\s*)(\d+)", re.M)
    m = pat.search(s)
    if not m:
        print(f"!! wkcc.wk 缺少 {k}")
        continue
    if m.group(2) != v:
        s = pat.sub(lambda mm: mm.group(1) + v, s, count=1)
        changed.append(f"{k}: {m.group(2)}->{v}")
open(p, "w", encoding="utf-8").write(s)
print("同步完成。变更:", "; ".join(changed) if changed else "（无变化）")
