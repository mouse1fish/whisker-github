# 1) runtime_x64.py：回环地址 rdata + rt_net_listen_loop
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
s = s.replace(
    '''    # SECURITY_ATTRIBUTES{ nLength=16, lpSecurityDescriptor=NULL, bInheritHandle=TRUE }''',
    '''    pe.rdata_item("str_loopback", b"127.0.0.1\\x00", align=1)
    # SECURITY_ATTRIBUTES{ nLength=16, lpSecurityDescriptor=NULL, bInheritHandle=TRUE }''')
anchor = '''    a.note("rt_net_accept(lsock) -> 客户端 socket / -1")'''
add = '''    a.note("rt_net_listen_loop(port) -> 监听 socket / -1（仅绑定 127.0.0.1）")
    a.label("rt_net_listen_loop")
    f = Frame(a)
    sl_s = f.alloc()
    sl_port = f.alloc()
    a.mov_mr(RSP, f.disp(sl_port), RCX)     # 先存端口（不能和 socket 共用槽！）
    a.call("rt_net_sock")
    a.cmp_ri(RAX, -1)
    a.jcc("ne", "rt_nll_have")
    a.mov_ri(RAX, -1)
    f.close()
    a.label("rt_nll_have")
    a.mov_mr(RSP, f.disp(sl_s), RAX)        # socket 存自己的槽
    a.lea_rip(RCX, "str_loopback")
    a.call_rip("imp_inet_addr")             # rax = 127.0.0.1（网络序 u32）
    a.mov_rr(RDX, RAX)
    a.mov_rm(RCX, RSP, f.disp(sl_port))
    a.call("rt_net_sin")
    a.mov_rm(RCX, RSP, f.disp(sl_s))
    a.lea_rip(RDX, "g_sin")
    a.mov_ri(R8, 16)
    a.call_rip("imp_bind")
    a.movsxd_rax_eax()
    a.cmp_ri(RAX, -1)
    a.jcc("ne", "rt_nll_bok")
    a.mov_rm(RCX, RSP, f.disp(sl_s))
    a.call_rip("imp_closesocket")
    a.movsxd_rax_eax()
    a.mov_ri(RAX, -1)
    f.close()
    a.label("rt_nll_bok")
    a.mov_rm(RCX, RSP, f.disp(sl_s))
    a.mov_ri(RDX, 16)                       # backlog
    a.call_rip("imp_listen")
    a.movsxd_rax_eax()
    a.cmp_ri(RAX, -1)
    a.jcc("ne", "rt_nll_lok")
    a.mov_rm(RCX, RSP, f.disp(sl_s))
    a.call_rip("imp_closesocket")
    a.movsxd_rax_eax()
    a.mov_ri(RAX, -1)
    f.close()
    a.label("rt_nll_lok")
    a.mov_rm(RAX, RSP, f.disp(sl_s))
    f.close()

    a.note("rt_net_accept(lsock) -> 客户端 socket / -1")'''
s = s.replace(anchor, add, 1)
open(p, "w", encoding="utf-8").write(s)

# 2) sema.py：netListenLocal 签名
p2 = r"whiskerc/sema.py"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace(
    '"netListen": ([INT_TY], INT_TY),                    # 监听端口 -> 监听 socket/-1',
    '"netListen": ([INT_TY], INT_TY),                    # 监听端口 -> 监听 socket/-1\\n    "netListenLocal": ([INT_TY], INT_TY),               # 仅绑定 127.0.0.1 的监听 -> socket/-1')
open(p2, "w", encoding="utf-8").write(s2)

# 3) codegen_x64.py：值位置分发
p3 = r"whiskerc/codegen_x64.py"
s3 = open(p3, encoding="utf-8").read()
s3 = s3.replace(
    '"netListen", "netAccept", "netConnect", "netSend", "netRecv",',
    '"netListen", "netListenLocal", "netAccept", "netConnect", "netSend", "netRecv",')
s3 = s3.replace(
    '''        if name == "netAccept":                  # (监听 socket) -> 客户端 socket''',
    '''        if name == "netListenLocal":             # (端口) -> 监听 socket（仅回环）
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_net_listen_loop")
            return

        if name == "netAccept":                  # (监听 socket) -> 客户端 socket''')
open(p3, "w", encoding="utf-8").write(s3)
print("runtime/sema/codegen 三处完成")
