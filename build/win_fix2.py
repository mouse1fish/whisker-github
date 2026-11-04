p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
old = "import struct"
new = "import math\nimport struct"
assert old in s and "import math" not in s, "import"
s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("import math OK")
