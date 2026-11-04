# 1) sema.py：加两个 cast 签名
p1 = r"whiskerc/sema.py"
s = open(p1, encoding="utf-8").read()
s = s.replace(
    '''    "procFree": ([PTR_TY], VOID_TY),                    # 关闭进程块里的句柄
}''',
    '''    "procFree": ([PTR_TY], VOID_TY),                    # 关闭进程块里的句柄
    "ptrToInt": ([PTR_TY], INT_TY),                     # 指针 -> 整数（身份变换，句柄/地址算术用）
    "intToPtr": ([INT_TY], PTR_TY),                     # 整数 -> 指针（身份变换）
}''')
open(p1, "w", encoding="utf-8").write(s)

# 2) codegen_x64.py：值位置元组 + 分发（纯类型变换：参数已在 RAX，零机器码）
p2 = r"whiskerc/codegen_x64.py"
s = open(p2, encoding="utf-8").read()
s = s.replace(
    '''                          "netClose", "procSpawn", "procSpawnPipe",
                          "procRead", "procWait", "procFree"):''',
    '''                          "netClose", "procSpawn", "procSpawnPipe",
                          "procRead", "procWait", "procFree",
                          "ptrToInt", "intToPtr"):''')
s = s.replace(
    '''        if name == "netClose":                   # (socket)
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_net_close")
            return''',
    '''        if name == "netClose":                   # (socket)
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_net_close")
            return

        if name == "ptrToInt" or name == "intToPtr":
            # 纯类型层 cast：值已在 RAX，无机器码
            self.eval(e.args[0])
            return''')
open(p2, "w", encoding="utf-8").write(s)
print("Python 侧 cast 内置完成")
