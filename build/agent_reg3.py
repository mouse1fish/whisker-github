# sema
p3 = r"whiskerc/sema.py"
s3 = open(p3, encoding="utf-8").read()
old4 = '''    "ptrToInt": ([PTR_TY], INT_TY),                     # 指针 -> 整数（身份变换，句柄/地址算术用）'''
new4 = '''    # ---- agent 原语（EonOS：屏幕/鼠标/键盘）----
    "screenW": ([], INT_TY),                            # 屏幕宽
    "screenH": ([], INT_TY),                            # 屏幕高
    "mouseX": ([], INT_TY),                             # 光标 X
    "mouseY": ([], INT_TY),                             # 光标 Y
    "mouseMove": ([INT_TY, INT_TY], INT_TY),            # 移动光标
    "mouseDown": ([INT_TY], INT_TY),                    # 按下（1 左/2 右/3 中）
    "mouseUp": ([INT_TY], INT_TY),                      # 抬起
    "keyDown": ([INT_TY], INT_TY),                      # 按下虚拟键码
    "keyUp": ([INT_TY], INT_TY),                        # 抬起虚拟键码
    "keyVk": ([INT_TY], INT_TY),                        # 字符 -> VK（低字节 VK，高字节 shift）
    "screenshot": ([STR_TY], INT_TY),                   # 截屏写 BMP 文件
    "ptrToInt": ([PTR_TY], INT_TY),                     # 指针 -> 整数（身份变换，句柄/地址算术用）'''
assert old4 in s3, "sema 锚点"
s3 = s3.replace(old4, new4)
open(p3, "w", encoding="utf-8").write(s3)
print("sema OK")

# codegen
p4 = r"whiskerc/codegen_x64.py"
s4 = open(p4, encoding="utf-8").read()
old5 = '''                          "ptrToInt", "intToPtr"):'''
new5 = '''                          "ptrToInt", "intToPtr",
                          "mouseMove", "mouseDown", "mouseUp",
                          "keyDown", "keyUp", "keyVk", "screenshot"):'''
assert old5 in s4, "codegen 元组"
s4 = s4.replace(old5, new5)
old6 = '''            if e.name == "netErr":
                a.call("rt_net_err")
                return'''
new6 = '''            if e.name == "netErr":
                a.call("rt_net_err")
                return
            if e.name == "screenW":
                a.call("rt_screen_w")
                return
            if e.name == "screenH":
                a.call("rt_screen_h")
                return
            if e.name == "mouseX":
                a.call("rt_mouse_x")
                return
            if e.name == "mouseY":
                a.call("rt_mouse_y")
                return'''
assert old6 in s4, "codegen 零参"
s4 = s4.replace(old6, new6)
old7 = '''        if name == "ptrToInt" or name == "intToPtr":'''
new7 = '''        if name == "mouseMove":                  # (x, y)
            t0 = self.eval_to_temp(e.args[0])
            t1 = self.eval_to_temp(e.args[1])
            a.mov_rm(RCX, RSP, self.f.disp(t0))
            a.mov_rm(RDX, RSP, self.f.disp(t1))
            a.call("rt_mouse_move")
            return

        if name == "mouseDown" or name == "mouseUp":
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_mouse_down" if name == "mouseDown" else "rt_mouse_up")
            return

        if name == "keyDown" or name == "keyUp" or name == "keyVk":
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            if name == "keyDown":
                a.call("rt_key_down")
            elif name == "keyUp":
                a.call("rt_key_up")
            else:
                a.call("rt_key_vk")
            return

        if name == "screenshot":                 # (路径)
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_screenshot")
            return

        if name == "ptrToInt" or name == "intToPtr":'''
assert old7 in s4, "codegen 实现锚点"
s4 = s4.replace(old7, new7)
open(p4, "w", encoding="utf-8").write(s4)
print("codegen OK")
