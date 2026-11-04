import re
# 1) extract name_map
p = r"tools/extract_runtime.py"
s = open(p, encoding="utf-8").read()
old = '''        "rt_cmdline": "OFF_CMDLINE",'''
new = '''        "rt_cmdline": "OFF_CMDLINE",
        "rt_sin16": "OFF_SIN16", "rt_cos16": "OFF_COS16",
        "rt_win_open": "OFF_WIN_OPEN", "rt_win_present": "OFF_WIN_PRESENT",
        "rt_win_pump": "OFF_WIN_PUMP", "rt_win_close": "OFF_WIN_CLOSE",
        "rt_key_async": "OFF_KEY_ASYNC",'''
assert old in s, "name_map"; s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)

# 2) wkcc：OFF 占位 + 分发 + 数组扩容 + NIMP + inames 重排
p2 = r"tools/wkcc.wk"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace("    hintRVA: Int[64]\n    inames: Str[64]", "    hintRVA: Int[96]\n    inames: Str[96]")
m = re.search(r"^    OFF_CMDLINE: Int = \d+$", s2, re.M)
assert m, "OFF_CMDLINE"
add = '''
    # ---- 3D 引擎（窗口 + 定点三角）----
    OFF_SIN16: Int = 0
    OFF_COS16: Int = 0
    OFF_WIN_OPEN: Int = 0
    OFF_WIN_PRESENT: Int = 0
    OFF_WIN_PUMP: Int = 0
    OFF_WIN_CLOSE: Int = 0
    OFF_KEY_ASYNC: Int = 0'''
s2 = s2[:m.end()] + add + s2[m.end():]
old_d = '''                if name == "cmdline" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_CMDLINE); lastTy = "Str"; return
                }'''
new_d = old_d + '''
                # ---- 3D 引擎 ----
                if name == "winOpen" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_WIN_OPEN); lastTy = "Int"; return
                }
                if name == "winPresent" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_WIN_PRESENT); lastTy = "Int"; return
                }
                if name == "winPump" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_WIN_PUMP); lastTy = "Int"; return
                }
                if name == "winClose" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_WIN_CLOSE); lastTy = "Int"; return
                }
                if name == "keyAsync" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_KEY_ASYNC); lastTy = "Int"; return
                }
                if name == "sin16" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_SIN16); lastTy = "Int"; return
                }
                if name == "cos16" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_COS16); lastTy = "Int"; return
                }'''
assert old_d in s2, "vkcc 分发"
s2 = s2.replace(old_d, new_d)
# NIMP 更新
for key, val in (("NIMPORT", 66), ("NIMP_KERNEL32", 23), ("NIMP_WS2", 12), ("NIMP_USER32", 23), ("NIMP_GDI32", 8)):
    s2 = re.sub(rf"^    {key}: Int = \d+$", f"    {key}: Int = {val}", s2, count=1, flags=re.M)
# inames 重排：删 21..65 行，在 inames[20] 后插入新块
for i in range(21, 66):
    s2 = re.sub(rf"^        inames\[{i}\] = \"[^\"]*\"\n", "", s2, flags=re.M)
k32n = ["GetCommandLineA", "GetModuleHandleA"]
ws2 = ["WSAStartup","socket","inet_addr","htons","bind","listen","accept","connect","send","recv","closesocket","WSAGetLastError"]
u32o = ["GetDC","ReleaseDC","GetSystemMetrics","SetCursorPos","mouse_event","keybd_event","VkKeyScanA","GetCursorPos"]
u32n = ["RegisterClassExA","CreateWindowExA","DefWindowProcA","ShowWindow","UpdateWindow","GetClientRect","PeekMessageA","TranslateMessage","DispatchMessageA","GetAsyncKeyState","DestroyWindow","PostQuitMessage","LoadCursorA","BeginPaint","EndPaint"]
g32 = ["CreateCompatibleDC","CreateCompatibleBitmap","SelectObject","BitBlt","GetDIBits","DeleteDC","DeleteObject","StretchDIBits"]
rows = []
idx = 21
for nm in k32n + ws2 + u32o + u32n + g32:
    rows.append((idx, nm)); idx += 1
assert idx == 66, f"总项数 {idx}"
block = "".join(f'        inames[{i}] = "{n}"\n' for i, n in rows)
c = s2.count('        inames[20] = "SetHandleInformation"\n')
assert c == 2, f"锚点出现 {c} 次"
s2 = s2.replace('        inames[20] = "SetHandleInformation"\n', '        inames[20] = "SetHandleInformation"\n' + block)
open(p2, "w", encoding="utf-8").write(s2)

# 3) sema 签名
p3 = r"whiskerc/sema.py"
s3 = open(p3, encoding="utf-8").read()
old3 = '''    "cmdline": ([], STR_TY),                            # 完整命令行（ANSI 字符串）'''
new3 = '''    "cmdline": ([], STR_TY),                            # 完整命令行（ANSI 字符串）
    # ---- 3D 引擎（窗口 + 定点三角）----
    "sin16": ([INT_TY], INT_TY),                        # 定点正弦（16.16，256 步整圆）
    "cos16": ([INT_TY], INT_TY),                        # 定点余弦
    "winOpen": ([STR_TY, INT_TY, INT_TY], INT_TY),      # 开窗（标题, 宽, 高）-> 1/0
    "winPresent": ([PTR_TY, INT_TY, INT_TY], INT_TY),   # 推帧（BGRA 缓冲, 宽, 高）
    "winPump": ([], INT_TY),                            # 泵消息 -> 1 存活 / 0 退出
    "winClose": ([], INT_TY),                           # 关窗
    "keyAsync": ([INT_TY], INT_TY),                     # 异步按键状态（非 0 = 按下）'''
assert old3 in s3, "sema"; s3 = s3.replace(old3, new3)
open(p3, "w", encoding="utf-8").write(s3)

# 4) codegen
p4 = r"whiskerc/codegen_x64.py"
s4 = open(p4, encoding="utf-8").read()
s4 = s4.replace('''                          "mouseMove", "mouseDown", "mouseUp",
                          "keyDown", "keyUp", "keyVk", "screenshot"):''',
                '''                          "mouseMove", "mouseDown", "mouseUp",
                          "keyDown", "keyUp", "keyVk", "screenshot",
                          "sin16", "cos16", "keyAsync",
                          "winOpen", "winPresent", "winClose"):''')
s4 = s4.replace('''            if e.name == "screenW":
                a.call("rt_screen_w")
                return''',
                '''            if e.name == "winPump":
                a.call("rt_win_pump")
                return
            if e.name == "screenW":
                a.call("rt_screen_w")
                return''')
old4 = '''        if name == "mouseMove":                  # (x, y)'''
new4 = '''        if name == "winOpen":                    # (标题, 宽, 高)
            t0 = self.eval_to_temp(e.args[0])
            t1 = self.eval_to_temp(e.args[1])
            t2 = self.eval_to_temp(e.args[2])
            a.mov_rm(RCX, RSP, self.f.disp(t0))
            a.mov_rm(RDX, RSP, self.f.disp(t1))
            a.mov_rm(R8, RSP, self.f.disp(t2))
            a.call("rt_win_open")
            return

        if name == "winPresent":                 # (缓冲, 宽, 高)
            t0 = self.eval_to_temp(e.args[0])
            t1 = self.eval_to_temp(e.args[1])
            t2 = self.eval_to_temp(e.args[2])
            a.mov_rm(RCX, RSP, self.f.disp(t0))
            a.mov_rm(RDX, RSP, self.f.disp(t1))
            a.mov_rm(R8, RSP, self.f.disp(t2))
            a.call("rt_win_present")
            return

        if name == "winClose":
            a.call("rt_win_close")
            return

        if name == "sin16" or name == "cos16":
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_sin16" if name == "sin16" else "rt_cos16")
            return

        if name == "keyAsync":
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_key_async")
            return

        if name == "mouseMove":                  # (x, y)'''
assert old4 in s4, "codegen 实现锚点"
s4 = s4.replace(old4, new4, 1)
open(p4, "w", encoding="utf-8").write(s4)
print("全链登记完成")
