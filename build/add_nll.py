# 1) extract_runtime.py：登记新符号名
p = r"tools/extract_runtime.py"
s = open(p, encoding="utf-8").read()
s = s.replace(
    '''        "rt_net_listen": "OFF_NET_LISTEN", "rt_net_accept": "OFF_NET_ACCEPT",''',
    '''        "rt_net_listen": "OFF_NET_LISTEN", "rt_net_listen_loop": "OFF_NET_LISTEN_L",
        "rt_net_accept": "OFF_NET_ACCEPT",''')
open(p, "w", encoding="utf-8").write(s)

# 2) wkcc.wk：常量 + 分发
p2 = r"tools/wkcc.wk"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace(
    "    OFF_NET_LISTEN: Int = 3523",
    "    OFF_NET_LISTEN: Int = 3523\n    OFF_NET_LISTEN_L: Int = PLACEHOLDER_L")
s2 = s2.replace(
    '''                if name == "netAccept" {''',
    '''                if name == "netListenLocal" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_NET_LISTEN_L); lastTy = "Int"; return
                }
                if name == "netAccept" {''')
open(p2, "w", encoding="utf-8").write(s2)
print("占位完成")
