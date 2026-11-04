p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
# 1) 正弦表改名 g_sintab
old = '''    pe.data_item("g_sin", _sin)'''
new = '''    pe.data_item("g_sintab", _sin)'''
assert old in s, "表声明"; s = s.replace(old, new)
# 2) rt_sin16 的 lea 目标改名
old2 = '''    a.lea_rip(RAX, "g_sin")
    a.emit(0x8B, 0x04, 0x88)                # mov eax, [rax + rcx*4]'''
new2 = '''    a.lea_rip(RAX, "g_sintab")
    a.emit(0x8B, 0x04, 0x88)                # mov eax, [rax + rcx*4]'''
assert old2 in s, "lea"; s = s.replace(old2, new2)
open(p, "w", encoding="utf-8").write(s)
print("g_sin 重名修复 OK")
