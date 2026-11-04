import struct, math
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()

# ---------- 1) 导入 ----------
old = '''           "CreatePipe", "SetHandleInformation", "GetCommandLineA"]'''
new = '''           "CreatePipe", "SetHandleInformation", "GetCommandLineA", "GetModuleHandleA"]'''
assert old in s, "k32"; s = s.replace(old, new)
old = '''                  "LoadCursorA", "BeginPaint", "EndPaint"]'''
new = '''                  "LoadCursorA", "BeginPaint", "EndPaint"]
# 注：上面 user32 列表已含窗口 API（win3d 用）'''
if old not in s:
    old2 = '''                  "mouse_event", "keybd_event", "VkKeyScanA", "GetCursorPos"]
GDI32_IMPORTS = ["CreateCompatibleDC", "CreateCompatibleBitmap", "SelectObject",
                 "BitBlt", "GetDIBits", "DeleteDC", "DeleteObject"]'''
    new2 = '''                  "mouse_event", "keybd_event", "VkKeyScanA", "GetCursorPos",
                  "RegisterClassExA", "CreateWindowExA", "DefWindowProcA", "ShowWindow",
                  "UpdateWindow", "GetClientRect", "PeekMessageA", "TranslateMessage",
                  "DispatchMessageA", "GetAsyncKeyState", "DestroyWindow", "PostQuitMessage",
                  "LoadCursorA", "BeginPaint", "EndPaint"]
GDI32_IMPORTS = ["CreateCompatibleDC", "CreateCompatibleBitmap", "SelectObject",
                 "BitBlt", "GetDIBits", "DeleteDC", "DeleteObject", "StretchDIBits"]'''
    assert old2 in s, "user32/gdi32"; s = s.replace(old2, new2)

# ---------- 2) 数据项 ----------
old = '''    pe.data_item("g_pt", b"\\x00" * 8)        # POINT（GetCursorPos）'''
new = '''    pe.data_item("g_pt", b"\\x00" * 8)        # POINT（GetCursorPos）
    # ---- 窗口（3D 引擎呈现）----
    pe.data_item("g_hwnd", b"\\x00" * 8)
    pe.data_item("g_hdc", b"\\x00" * 8)
    pe.data_item("g_wndclass", b"\\x00" * 80)  # WNDCLASSEXA
    pe.data_item("g_msg", b"\\x00" * 64)       # MSG（x64 48 字节，留余量）
    pe.data_item("g_rect", b"\\x00" * 16)      # RECT
    pe.data_item("g_ps", b"\\x00" * 72)        # PAINTSTRUCT
    pe.rdata_item("str_wcls", b"whisker3d\\x00", align=1)
    # 定点正弦表：256 项 16.16（整圆）
    _sin = b"".join(struct.pack("<i", int(round(math.sin(i * 2 * math.pi / 256) * 65536))) for i in range(256))
    pe.data_item("g_sin", _sin)'''
assert old in s, "data"; s = s.replace(old, new)

# ---------- 3) 函数：插在 agent 区之前 ----------
anchor = '''    a.note("rt_screen_w / rt_screen_h（GetSystemMetrics）")'''
assert anchor in s, "agent 锚点"
block = '''    # ================= 3D 引擎：窗口 + 定点三角 =================
    a.note("rt_sin16 / rt_cos16：定点正弦（16.16，256 步整圆）")
    a.label("rt_cos16")
    a.add_ri(RCX, 64)
    a.jmp("rt_sin16")

    a.label("rt_sin16")                     # rcx = 角度 0..255 -> 16.16
    f = Frame(a)
    a.and_ri(RCX, 255)
    a.lea_rip(RAX, "g_sin")
    a.emit(0x8B, 0x04, 0x88)                # mov eax, [rax + rcx*4]
    a.movsxd_rax_eax()
    f.close()

    # WndProc：WM_DESTROY/WM_CLOSE -> PostQuitMessage；WM_PAINT -> Begin/EndPaint；
    #          WM_ERASEBKGND -> 1；其余 DefWindowProcA
    a.note("rt_wndproc")
    a.label("rt_wndproc")
    f = Frame(a)
    sl_hwnd = f.alloc()
    sl_msg = f.alloc()
    a.mov_mr(RSP, f.disp(sl_hwnd), RCX)
    a.mov_mr(RSP, f.disp(sl_msg), RDX)
    a.cmp_ri(RDX, 2)                        # WM_DESTROY
    a.jcc("ne", "rt_wp_c1")
    a.xor_rr(RCX, RCX)
    a.call_rip("imp_PostQuitMessage")
    a.xor_rr(RAX, RAX)
    f.close()
    a.label("rt_wp_c1")
    a.cmp_ri(RDX, 0x10)                     # WM_CLOSE
    a.jcc("ne", "rt_wp_c2")
    a.mov_rm(RCX, RSP, f.disp(sl_hwnd))
    a.call_rip("imp_DestroyWindow")
    a.xor_rr(RAX, RAX)
    f.close()
    a.label("rt_wp_c2")
    a.cmp_ri(RDX, 0x0F)                     # WM_PAINT
    a.jcc("ne", "rt_wp_c3")
    a.mov_rm(RCX, RSP, f.disp(sl_hwnd))
    a.lea_rip(RDX, "g_ps")
    a.call_rip("imp_BeginPaint")
    a.mov_rm(RCX, RSP, f.disp(sl_hwnd))
    a.lea_rip(RDX, "g_ps")
    a.call_rip("imp_EndPaint")
    a.xor_rr(RAX, RAX)
    f.close()
    a.label("rt_wp_c3")
    a.cmp_ri(RDX, 0x14)                     # WM_ERASEBKGND
    a.jcc("ne", "rt_wp_dflt")
    a.mov_ri(RAX, 1)
    f.close()
    a.label("rt_wp_dflt")
    a.mov_rm(RCX, RSP, f.disp(sl_hwnd))
    a.mov_rm(RDX, RSP, f.disp(sl_msg))
    a.mov_rr(R8, R8)
    a.mov_rr(R9, R9)
    a.call_rip("imp_DefWindowProcA")
    f.close()

    # rt_win_open(title, w, h) -> 1/0
    a.note("rt_win_open / rt_win_present / rt_win_pump / rt_win_close / rt_key_async")
    a.label("rt_win_open")
    f = Frame(a, nextra=8, saved=(RDI,))
    sl_t = f.alloc()
    sl_w = f.alloc()
    sl_h = f.alloc()
    a.mov_mr(RSP, f.disp(sl_t), RCX)
    a.mov_mr(RSP, f.disp(sl_w), RDX)
    a.mov_mr(RSP, f.disp(sl_h), R8)
    # WNDCLASSEXA 清零并填字段
    a.lea_rip(RCX, "g_wndclass")
    a.mov_ri(RDX, 80)
    a.call("rt_zero")
    a.lea_rip(RAX, "g_wndclass")
    a.mov_mi(RAX, 0, 80)                    # cbSize
    a.mov_mi(RAX, 4, 3)                     # CS_HREDRAW|CS_VREDRAW
    a.lea_rip_code(RCX, "rt_wndproc")
    a.mov_mr(RAX, 8, RCX)                   # lpfnWndProc
    a.xor_rr(RCX, RCX)
    a.call_rip("imp_GetModuleHandleA")
    a.lea_rip(RCX, "g_wndclass")
    a.mov_mr(RCX, 24, RAX)                  # hInstance
    a.xor_rr(RCX, RCX)
    a.mov_ri(RDX, 32512)                    # IDC_ARROW
    a.call_rip("imp_LoadCursorA")
    a.lea_rip(RCX, "g_wndclass")
    a.mov_mr(RCX, 40, RAX)                  # hCursor
    a.lea_rip(RAX, "str_wcls")
    a.mov_mr(RCX, 64, RAX)                  # lpszClassName
    a.lea_rip(RCX, "g_wndclass")
    a.call_rip("imp_RegisterClassExA")
    a.cmp_ri(RAX, 0)
    a.jcc("ne", "rt_wo_ok")
    a.xor_rr(RAX, RAX)
    f.close()
    a.label("rt_wo_ok")
    # CreateWindowExA(0, cls, title, style, CW, CW, w, h, 0,0, hInst, 0)
    a.xor_rr(RCX, RCX)
    a.lea_rip(RDX, "str_wcls")
    a.mov_rm(R8, RSP, f.disp(sl_t))
    a.mov_ri(R9, 0x10CF0000)                # WS_OVERLAPPEDWINDOW | WS_VISIBLE
    a.mov_ri(RAX, 0x80000000)
    a.mov_mr(RSP, f.extra_disp(0), RAX)     # X = CW_USEDEFAULT
    a.mov_mr(RSP, f.extra_disp(1), RAX)     # Y
    a.mov_rm(RAX, RSP, f.disp(sl_w))
    a.mov_mr(RSP, f.extra_disp(2), RAX)     # nWidth
    a.mov_rm(RAX, RSP, f.disp(sl_h))
    a.mov_mr(RSP, f.extra_disp(3), RAX)     # nHeight
    a.mov_mi(RSP, f.extra_disp(4), 0)       # hWndParent
    a.mov_mi(RSP, f.extra_disp(5), 0)       # hMenu
    a.lea_rip(RAX, "g_wndclass")
    a.mov_rm(RAX, RAX, 24)
    a.mov_mr(RSP, f.extra_disp(6), RAX)     # hInstance
    a.mov_mi(RSP, f.extra_disp(7), 0)       # lpParam
    a.call_rip("imp_CreateWindowExA")
    a.mov_rip_r("g_hwnd", RAX)
    a.cmp_ri(RAX, 0)
    a.jcc("ne", "rt_wo_cw2")
    a.xor_rr(RAX, RAX)
    f.close()
    a.label("rt_wo_cw2")
    a.mov_rr(RCX, RAX)
    a.mov_ri(RDX, 5)                        # SW_SHOW
    a.call_rip("imp_ShowWindow")
    a.mov_r_rip(RCX, "g_hwnd")
    a.call_rip("imp_UpdateWindow")
    a.mov_r_rip(RCX, "g_hwnd")
    a.call_rip("imp_GetDC")
    a.mov_rip_r("g_hdc", RAX)
    a.mov_ri(RAX, 1)
    f.close()

    # rt_win_present(fb, w, h) -> 像素数 / -1
    a.label("rt_win_present")
    f = Frame(a, nextra=9, saved=(RDI,))
    sl_fb = f.alloc()
    sl_w2 = f.alloc()
    sl_h2 = f.alloc()
    a.mov_mr(RSP, f.disp(sl_fb), RCX)
    a.mov_mr(RSP, f.disp(sl_w2), RDX)
    a.mov_mr(RSP, f.disp(sl_h2), R8)
    # g_bmi：40 字节头，height 取负 = top-down
    a.lea_rip(RCX, "g_bmi")
    a.mov_ri(RDX, 40)
    a.call("rt_zero")
    a.lea_rip(RAX, "g_bmi")
    a.mov_mi(RAX, 0, 40)
    a.mov_rm(RCX, RSP, f.disp(sl_w2))
    a.mov_mr(RAX, 4, RCX)
    a.mov_rm(RCX, RSP, f.disp(sl_h2))
    a.neg_r(RCX)
    a.mov_mr(RAX, 8, RCX)
    a.mov_mi(RAX, 12, 1)
    a.mov_mi(RAX, 14, 32)
    # GetClientRect
    a.mov_r_rip(RCX, "g_hwnd")
    a.lea_rip(RDX, "g_rect")
    a.call_rip("imp_GetClientRect")
    # StretchDIBits(hdc, 0,0,cw,ch, 0,0,w,h, fb, &bmi, 0, SRCCOPY)
    a.mov_r_rip(RCX, "g_hdc")
    a.xor_rr(RDX, RDX)
    a.xor_rr(R8, R8)
    a.lea_rip(RAX, "g_rect")
    a.mov_rm(R9, RAX, 8)                    # cw = right
    a.mov_rm(RAX, RAX, 12)                  # ch = bottom
    a.mov_mr(RSP, f.extra_disp(0), RAX)
    a.mov_mi(RSP, f.extra_disp(1), 0)       # xSrc
    a.mov_mi(RSP, f.extra_disp(2), 0)       # ySrc
    a.mov_rm(RAX, RSP, f.disp(sl_w2))
    a.mov_mr(RSP, f.extra_disp(3), RAX)     # wSrc
    a.mov_rm(RAX, RSP, f.disp(sl_h2))
    a.mov_mr(RSP, f.extra_disp(4), RAX)     # hSrc
    a.mov_rm(RAX, RSP, f.disp(sl_fb))
    a.mov_mr(RSP, f.extra_disp(5), RAX)     # lpBits
    a.lea_rip(RAX, "g_bmi")
    a.mov_mr(RSP, f.extra_disp(6), RAX)     # lpbmi
    a.mov_mi(RSP, f.extra_disp(7), 0)       # iUsage
    a.mov_mi(RSP, f.extra_disp(8), 0xCC0020)  # SRCCOPY
    a.call_rip("imp_StretchDIBits")
    a.movsxd_rax_eax()
    f.close()

    # rt_win_pump() -> 1 存活 / 0 收到 WM_QUIT
    a.label("rt_win_pump")
    f = Frame(a)
    a.label("rt_wp_loop")
    a.lea_rip(RCX, "g_msg")
    a.xor_rr(RDX, RDX)
    a.xor_rr(R8, R8)
    a.xor_rr(R9, R9)
    a.mov_mi(RSP, f.extra_disp(0), 1)       # PM_REMOVE
    a.call_rip("imp_PeekMessageA")
    a.test_rr(RAX, RAX)
    a.jcc("ne", "rt_wp_msg")
    a.mov_ri(RAX, 1)
    f.close()
    a.label("rt_wp_msg")
    a.lea_rip(RAX, "g_msg")
    a.mov_rm(RCX, RAX, 8)                   # MSG.message
    a.cmp_ri(RCX, 0x12)                     # WM_QUIT
    a.jcc("ne", "rt_wp_disp")
    a.xor_rr(RAX, RAX)
    f.close()
    a.label("rt_wp_disp")
    a.lea_rip(RCX, "g_msg")
    a.call_rip("imp_TranslateMessage")
    a.lea_rip(RCX, "g_msg")
    a.call_rip("imp_DispatchMessageA")
    a.jmp("rt_wp_loop")

    # rt_win_close() -> 0
    a.label("rt_win_close")
    f = Frame(a)
    a.mov_r_rip(RCX, "g_hwnd")
    a.mov_r_rip(RDX, "g_hdc")
    a.call_rip("imp_ReleaseDC")
    a.mov_r_rip(RCX, "g_hwnd")
    a.call_rip("imp_DestroyWindow")
    a.xor_rr(RAX, RAX)
    f.close()

    # rt_key_async(vk) -> 0x8000 位（非 0 = 当前按下）
    a.label("rt_key_async")
    f = Frame(a)
    a.call_rip("imp_GetAsyncKeyState")
    a.and_ri(RAX, 0x8000)
    f.close()

'''
s = s.replace(anchor, block + anchor, 1)
open(p, "w", encoding="utf-8").write(s)
print("runtime 窗口/定点函数写入完成")
