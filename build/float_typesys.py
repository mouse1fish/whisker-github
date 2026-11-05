# 1) typesys.py：FLOAT 类型
p = r"whiskerc/typesys.py"
s = open(p, encoding="utf-8").read()
old = "INT_TY = Ty(INT)"
new = "INT_TY = Ty(INT)\nFLOAT_TY = Ty(FLOAT)"
assert old in s, "INT_TY"
s = s.replace(old, new, 1)
# FLOAT 常量（如果 FLOAT 字符串不存在）
if '"FLOAT"' not in s and "'FLOAT'" not in s:
    # 找 INT = "Int" 或类似的常量定义
    m = re.search(r'^INT\s*=\s*"(\w+)"', s, re.M)
    if m:
        s = s.replace(f'{m.group(1)} = "{m.group(1)}"', f'{m.group(1)} = "{m.group(1)}"\nFLOAT = "Float"', 1)
    else:
        # 可能是 INT = "Int" 的形式
        m2 = re.search(r'^INT\s*=\s*', s, re.M)
        if m2:
            line_start = m2.start()
            line_end = s.index('\n', line_start)
            int_line = s[line_start:line_end]
            # INT = Ty("Int") 或 INT = "Int"
            float_line = int_line.replace("INT", "FLOAT").replace('"Int"', '"Float"')
            s = s[:line_start] + float_line + "\n" + s[line_start:]
            print(f"FLOAT 常量: {float_line}")
open(p, "w", encoding="utf-8").write(s)
print("typesys OK")
