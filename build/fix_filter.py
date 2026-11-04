p = r"tools/extract_runtime.py"
s = open(p, encoding="utf-8").read()
s = s.replace(
    "        if wk and not name.endswith((\"_ok\", \"_slow\", \"_have\", \"_loop\", \"_done\")):",
    "        if wk:")
open(p, "w", encoding="utf-8").write(s)
print("过滤规则已修")
