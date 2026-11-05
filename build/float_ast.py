import re
# A) ast_nodes.py：FloatLit
p = r"whiskerc/ast_nodes.py"
s = open(p, encoding="utf-8").read()
m = re.search(r"(class IntLit\(Expr\):[\s\S]*?)(\nclass )", s)
assert m, "IntLit"
floatlit = m.group(1).replace("IntLit", "FloatLit").replace("value: int", "value: int  # IEEE 754 bits")
s = s[:m.end(1)] + "\n\n" + floatlit + s[m.end(1):]
open(p, "w", encoding="utf-8").write(s)
print("ast_nodes FloatLit OK")

# B) parser.py：float token → FloatLit；Float 类型名
p2 = r"whiskerc/parser.py"
s2 = open(p2, encoding="utf-8").read()
old = 'if t.kind == "int":'
assert old in s2
new = '''if t.kind == "float":
            import struct as _s
            bits = _s.unpack("<Q", _s.pack("<d", float(t.text)))[0]
            return A.FloatLit(bits, t.line, t.col)
        if t.kind == "int":'''
s2 = s2.replace(old, new, 1)
open(p2, "w", encoding="utf-8").write(s2)
print("parser OK")

# C) sema.py：import FLOAT_TY + BUILTIN_SIGS + 类型检查
p3 = r"whiskerc/sema.py"
s3 = open(p3, encoding="utf-8").read()
s3 = s3.replace(
    "from .typesys import (BOOL_TY, ERROR_TY, INT_TY, PTR_TY, STR_TY, VOID,",
    "from .typesys import (BOOL_TY, ERROR_TY, FLOAT_TY, INT_TY, PTR_TY, STR_TY, VOID,")
# builtin sigs
old3 = '''    "ptrToInt": ([PTR_TY], INT_TY),'''
new3 = '''    "itof": ([INT_TY], FLOAT_TY),                       # Int -> Float
    "ftoi": ([FLOAT_TY], INT_TY),                       # Float -> Int（截断）
    "ptrToInt": ([PTR_TY], INT_TY),'''
assert old3 in s3, "sema sigs"; s3 = s3.replace(old3, new3)
open(p3, "w", encoding="utf-8").write(s3)
print("sema OK")
