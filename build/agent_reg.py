# A1) extract_runtime.py：新符号名映射
p = r"tools/extract_runtime.py"
s = open(p, encoding="utf-8").read()
old = '''        "rt_proc_free": "OFF_PROC_FREE",
    }'''
new = '''        "rt_proc_free": "OFF_PROC_FREE",
        "rt_screen_w": "OFF_SCREEN_W", "rt_screen_h": "OFF_SCREEN_H",
        "rt_mouse_x": "OFF_MOUSE_X", "rt_mouse_y": "OFF_MOUSE_Y",
        "rt_mouse_move": "OFF_MOUSE_MOVE", "rt_mouse_down": "OFF_MOUSE_DOWN",
        "rt_mouse_up": "OFF_MOUSE_UP", "rt_key_down": "OFF_KEY_DOWN",
        "rt_key_up": "OFF_KEY_UP", "rt_key_vk": "OFF_KEY_VK",
        "rt_screenshot": "OFF_SCREENSHOT",
    }'''
assert old in s, "name_map"; s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)

# A2) wkcc.wk：数组扩容 + OFF 占位行 + 分发
p2 = r"tools/wkcc.wk"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace("    hintRVA: Int[40]\n    inames: Str[40]", "    hintRVA: Int[64]\n    inames: Str[64]")
old2 = "    OFF_PROC_FREE: Int = 4679"
new2 = '''    OFF_PROC_FREE: Int = 4679
    # ---- agent 原语（EonOS：屏幕/鼠标/键盘）----
    OFF_SCREEN_W: Int = 0
    OFF_SCREEN_H: Int = 0
    OFF_MOUSE_X: Int = 0
    OFF_MOUSE_Y: Int = 0
    OFF_MOUSE_MOVE: Int = 0
    OFF_MOUSE_DOWN: Int = 0
    OFF_MOUSE_UP: Int = 0
    OFF_KEY_DOWN: Int = 0
    OFF_KEY_UP: Int = 0
    OFF_KEY_VK: Int = 0
    OFF_SCREENSHOT: Int = 0'''
assert old2 in s2, "OFF_PROC_FREE"; s2 = s2.replace(old2, new2)
old3 = '''                if name == "procFree" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_PROC_FREE); lastTy = "Int"; return
                }'''
new3 = old3 + '''
                # ---- agent 原语（EonOS）----
                if name == "screenW" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_SCREEN_W); lastTy = "Int"; return
                }
                if name == "screenH" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_SCREEN_H); lastTy = "Int"; return
                }
                if name == "mouseX" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_MOUSE_X); lastTy = "Int"; return
                }
                if name == "mouseY" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_MOUSE_Y); lastTy = "Int"; return
                }
                if name == "mouseMove" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_MOUSE_MOVE); lastTy = "Int"; return
                }
                if name == "mouseDown" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_MOUSE_DOWN); lastTy = "Int"; return
                }
                if name == "mouseUp" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_MOUSE_UP); lastTy = "Int"; return
                }
                if name == "keyDown" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_KEY_DOWN); lastTy = "Int"; return
                }
                if name == "keyUp" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_KEY_UP); lastTy = "Int"; return
                }
                if name == "keyVk" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_KEY_VK); lastTy = "Int"; return
                }
                if name == "screenshot" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_SCREENSHOT); lastTy = "Int"; return
                }'''
assert old3 in s2, "procFree 分发"; s2 = s2.replace(old3, new3)
open(p2, "w", encoding="utf-8").write(s2)

# A3) sema.py 签名
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
assert old4 in s3, "sema 锚点"; s3 = s3.replace(old4, new4)
open(p3, "w", encoding="utf-8").write(s3)

# A4) codegen：元组 + 实现
p4 = r"whiskerc/codegen_x64.py"
s4 = open(p4, encoding="utf-8").read()
old5 = '''                          "ptrToInt", "intToPtr"):'''
new5 = '''                          "ptrToInt", "intToPtr",
                          "mouseMove", "mouseDown", "mouseUp",
                          "keyDown", "keyUp", "keyVk", "screenshot"):'''
assert old5 in s4, "codegen 元组"; s4 = s4.replace(old5, new5)
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
assert old6 in s4, "codegen 零参"; s4 = s4.replace(old6, new6)
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
assert old7 in s4, "codegen 实现锚点"; s4 = s4.replace(old7, new7)
open(p4, "w", encoding="utf-8").write(s4)
print("双侧编译器登记完成")
