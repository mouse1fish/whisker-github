import re
# A) runtime：kernel32 追加 GetCommandLineA + rt_cmdline
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
old = '''           "CreatePipe", "SetHandleInformation"]'''
new = '''           "CreatePipe", "SetHandleInformation", "GetCommandLineA"]'''
assert old in s, "IMPORTS"; s = s.replace(old, new)
old = '''    a.note("rt_screen_w / rt_screen_h（GetSystemMetrics）")'''
new = '''    a.note("rt_cmdline() -> 完整命令行字符串（GetCommandLineA，ANSI）")
    a.label("rt_cmdline")
    f = Frame(a)
    a.call_rip("imp_GetCommandLineA")
    f.close()

    a.note("rt_screen_w / rt_screen_h（GetSystemMetrics）")'''
assert old in s, "rt_cmdline 锚点"; s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("runtime OK")

# B) extract name_map
p2 = r"tools/extract_runtime.py"
s2 = open(p2, encoding="utf-8").read()
old2 = '''        "rt_screen_w": "OFF_SCREEN_W", "rt_screen_h": "OFF_SCREEN_H",'''
new2 = '''        "rt_cmdline": "OFF_CMDLINE",
        "rt_screen_w": "OFF_SCREEN_W", "rt_screen_h": "OFF_SCREEN_H",'''
assert old2 in s2, "name_map"; s2 = s2.replace(old2, new2)
open(p2, "w", encoding="utf-8").write(s2)
print("extract OK")

# C) sema 签名
p3 = r"whiskerc/sema.py"
s3 = open(p3, encoding="utf-8").read()
old3 = '''    # ---- agent 原语（EonOS：屏幕/鼠标/键盘）----'''
new3 = '''    "cmdline": ([], STR_TY),                            # 完整命令行（ANSI 字符串）
    # ---- agent 原语（EonOS：屏幕/鼠标/键盘）----'''
assert old3 in s3, "sema"; s3 = s3.replace(old3, new3)
open(p3, "w", encoding="utf-8").write(s3)
print("sema OK")

# D) codegen 零参
p4 = r"whiskerc/codegen_x64.py"
s4 = open(p4, encoding="utf-8").read()
old4 = '''            if e.name == "screenW":'''
new4 = '''            if e.name == "cmdline":
                a.call("rt_cmdline")
                return
            if e.name == "screenW":'''
assert old4 in s4, "codegen"; s4 = s4.replace(old4, new4)
open(p4, "w", encoding="utf-8").write(s4)
print("codegen OK")

# E) wkcc：OFF_CMDLINE 占位 + 分发 + inames 重排（kernel32 22 项）+ NIMP_KERNEL32
p5 = r"tools/wkcc.wk"
s5 = open(p5, encoding="utf-8").read()
m = re.search(r"^    OFF_SCREEN_W: Int = \d+$", s5, re.M)
assert m, "OFF_SCREEN_W"
s5 = s5[:m.start()] + "    OFF_CMDLINE: Int = 0\n" + s5[m.start():]
old5 = '''                # ---- agent 原语（EonOS）----'''
new5 = '''                if name == "cmdline" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_CMDLINE); lastTy = "Str"; return
                }
                # ---- agent 原语（EonOS）----'''
assert old5 in s5, "wkcc 分发"; s5 = s5.replace(old5, new5)
# NIMP_KERNEL32 21 -> 22
m2 = re.search(r"^    NIMP_KERNEL32: Int = \d+$", s5, re.M)
assert m2, "NIMP_KERNEL32"
s5 = s5[:m2.start()] + "    NIMP_KERNEL32: Int = 22" + s5[m2.end():]
# inames 重排：在两处 inames 块重写 21..48（插入 GetCommandLineA，其余顺延）
k32 = ["GetCommandLineA"]
ws2 = ["WSAStartup","socket","inet_addr","htons","bind","listen","accept","connect","send","recv","closesocket","WSAGetLastError"]
u32 = ["GetDC","ReleaseDC","GetSystemMetrics","SetCursorPos","mouse_event","keybd_event","VkKeyScanA","GetCursorPos"]
g32 = ["CreateCompatibleDC","CreateCompatibleBitmap","SelectObject","BitBlt","GetDIBits","DeleteDC","DeleteObject"]
lines = []
idx = 21
lines.append((idx, "GetCommandLineA")); idx += 1
for nm in ws2:
    lines.append((idx, nm)); idx += 1
for nm in u32:
    lines.append((idx, nm)); idx += 1
for nm in g32:
    lines.append((idx, nm)); idx += 1
block = "".join(f'        inames[{i}] = "{n}"\n' for i, n in lines)
# 删掉旧 21..48 行，再在 inames[20] 行后插入新块
for i in range(21, 49):
    s5 = re.sub(rf"^        inames\[{i}\] = \"[^\"]*\"\n", "", s5, flags=re.M)
c = s5.count('        inames[20] = "SetHandleInformation"\n')
assert c == 2, f"inames[20] 出现 {c} 次"
s5 = s5.replace('        inames[20] = "SetHandleInformation"\n', '        inames[20] = "SetHandleInformation"\n' + block)
open(p5, "w", encoding="utf-8").write(s5)
print("wkcc OK（inames 重排 + NIMP_KERNEL32=22）")
