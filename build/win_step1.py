import struct, math
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()

# 1) 导入：kernel32 + GetModuleHandleA；user32 窗口组；gdi32 + StretchDIBits
old = '''           "CreatePipe", "SetHandleInformation", "GetCommandLineA"]'''
new = '''           "CreatePipe", "SetHandleInformation", "GetCommandLineA", "GetModuleHandleA"]'''
assert old in s, "k32"; s = s.replace(old, new)

old = '''USER32_IMPORTS = ["GetDC", "ReleaseDC", "GetSystemMetrics", "SetCursorPos",
                  "mouse_event", "keybd_event", "VkKeyScanA", "GetCursorPos"]
GDI32_IMPORTS = ["CreateCompatibleDC", "CreateCompatibleBitmap", "SelectObject",
                 "BitBlt", "GetDIBits", "DeleteDC", "DeleteObject"]'''
new = '''USER32_IMPORTS = ["GetDC", "ReleaseDC", "GetSystemMetrics", "SetCursorPos",
                  "mouse_event", "keybd_event", "VkKeyScanA", "GetCursorPos",
                  "RegisterClassExA", "CreateWindowExA", "DefWindowProcA", "ShowWindow",
                  "UpdateWindow", "GetClientRect", "PeekMessageA", "TranslateMessage",
                  "DispatchMessageA", "GetAsyncKeyState", "DestroyWindow", "PostQuitMessage",
                  "LoadCursorA", "BeginPaint", "EndPaint"]
GDI32_IMPORTS = ["CreateCompatibleDC", "CreateCompatibleBitmap", "SelectObject",
                 "BitBlt", "GetDIBits", "DeleteDC", "DeleteObject", "StretchDIBits"]'''
assert old in s, "user32/gdi32"; s = s.replace(old, new)

# 2) 数据项：窗口状态 + 正弦表
old = '''    pe.data_item("g_pt", b"\\x00" * 8)        # POINT（GetCursorPos）'''
new = '''    pe.data_item("g_pt", b"\\x00" * 8)        # POINT（GetCursorPos）
    # ---- 窗口（3D 引擎呈现）----
    pe.data_item("g_hwnd", b"\\x00" * 8)
    pe.data_item("g_hdc", b"\\x00" * 8)
    pe.data_item("g_wndclass", b"\\x00" * 80)  # WNDCLASSEXA
    pe.data_item("g_msg", b"\\x00" * 48)       # MSG（x64 56 字节，留余量）
    pe.data_item("g_rect", b"\\x00" * 16)      # RECT
    pe.data_item("g_ps", b"\\x00" * 72)        # PAINTSTRUCT
    pe.rdata_item("str_wcls", b"whisker3d\\x00", align=1)
    # 定点正弦表：256 项，16.16（angle 0..255 → 整圆）
    sin_vals = []
    for i in range(256):
        sin_vals.append(int(round(math.sin(i * 2 * math.pi / 256) * 65536)))
    pe.data_item("g_sin", b"".join(struct.pack("<i", v) for v in sin_vals))'''
assert old in s, "data"; s = s.replace(old, new)

# 3) 窗口/定点函数（追加在 agent 原语区末尾：rt_screenshot 之后）
old = '''    # 读盘发文件（web 根：G:/trea-Eon-os/eonos/web/）'''
assert old not in s  # 那是 httpd.wk，不在这
anchor = '''    # rt_screenshot（GetDC/BitBlt/GetDIBits -> BMP 文件）'''
m = anchor + s.split(anchor,1)[1][:s.split(anchor,1)[1].index("    a.note(\"rt_screenshot")]
add = '''
    # ================= 3D 引擎支持：窗口 + 定点三角 =================
    a.note("rt_sin16/rt_cos16：定点正弦（16.16，256 步整圆）")
    a.label("rt_sin16")                     # rcx = 角度 0..255
    f = Frame(a)
    a.and_ri(RCX, 255)
    a.lea_rip(RAX, "g_sin")
    a.mov_rm(RAX, RAX, 0)                   # 占位：下面改为 [rax+rcx*4]
    f.close()
'''
# 上面占位不适用（mov_rm 无变址），改为手写指令实现
s = s.replace(m, m)  # no-op 保持锚点
open(p, "w", encoding="utf-8").write(s)
print("runtime 导入与数据项就绪（函数体下一步）")
