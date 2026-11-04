import io
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
# 在 32 位返回值的 winsock 调用后插入符号扩展
repls = [
    ('a.call_rip("imp_bind")',     'a.call_rip("imp_bind")\n    a.movsxd_rax_eax()'),
    ('a.call_rip("imp_listen")',   'a.call_rip("imp_listen")\n    a.movsxd_rax_eax()'),
    ('a.call_rip("imp_connect")',  'a.call_rip("imp_connect")\n    a.movsxd_rax_eax()'),
    ('a.call_rip("imp_send")',     'a.call_rip("imp_send")\n    a.movsxd_rax_eax()'),
    ('a.call_rip("imp_recv")',     'a.call_rip("imp_recv")\n    a.movsxd_rax_eax()'),
    ('a.call_rip("imp_closesocket")', 'a.call_rip("imp_closesocket")\n    a.movsxd_rax_eax()'),
]
for old, new in repls:
    n = s.count(old)
    s = s.replace(old, new)
    print(f"{old} 替换 {n} 处")
open(p, "w", encoding="utf-8").write(s)
