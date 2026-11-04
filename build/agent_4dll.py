import re
p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()

# 1) 导入表段：双 DLL → 四 DLL
old = '''        # ---- 9) .rdata 段：blob rdata + 导入表（双 DLL）+ 字符串 ----
        # 布局（与 whiskerc/pe_x64.py 的 _build_import_items 一致）：
        #   描述符数组 3×20B（kernel32 / ws2_32 / 全零终止）
        #   ILT0(K+1)×8B → ILT1(W+1)×8B → dll 名 ×2 → hint-name（扁平顺序）
        #   IAT 复用 blob .data 里的 __iat__ 槽位（槽位序 = inames 扁平序）
        w = 512 + textRaw
        putBlob(RT_TEXT_LEN, RT_RDATA_LEN)    # blob rdata
        impBase: Int = RT_RDATA_LEN
        nk: Int = NIMP_KERNEL32
        nw: Int = NIMPORT - NIMP_KERNEL32
        descRVA: Int = RDATA_RVA + impBase
        ilt0RVA: Int = descRVA + 60
        ilt1RVA: Int = ilt0RVA + 8 * (nk + 1)
        dll0RVA: Int = ilt1RVA + 8 * (nw + 1)
        dll1RVA: Int = dll0RVA + 13             # "kernel32.dll\\0" = 13 字节
        hint0RVA: Int = dll1RVA + 11            # "ws2_32.dll\\0" = 11 字节
        # 描述符：kernel32（IAT 首槽 = 0）、ws2_32（IAT 首槽 = 第 nk 槽）、终止符
        put32(ilt0RVA); put32(0); put32(0); put32(dll0RVA); put32(DATA_RVA + IAT_IN_DATA)
        put32(ilt1RVA); put32(0); put32(0); put32(dll1RVA); put32(DATA_RVA + IAT_IN_DATA + 8 * nk)
        put32(0); put32(0); put32(0); put32(0); put32(0)'''
new = '''        # ---- 9) .rdata 段：blob rdata + 导入表（四 DLL：kernel32/ws2_32/user32/gdi32）+ 字符串 ----
        # 布局（与 whiskerc/pe_x64.py 的 _build_import_items 一致）：
        #   描述符数组 5×20B（4 DLL + 全零终止）
        #   ILT0..3 顺序排列 → 4 个 dll 名 → hint-name（扁平顺序）
        #   IAT 复用 blob .data 里的 __iat__ 槽位（槽位序 = inames 扁平序）
        w = 512 + textRaw
        putBlob(RT_TEXT_LEN, RT_RDATA_LEN)    # blob rdata
        impBase: Int = RT_RDATA_LEN
        nk: Int = NIMP_KERNEL32
        nw: Int = NIMP_WS2
        nu: Int = NIMP_USER32
        ng: Int = NIMP_GDI32
        descRVA: Int = RDATA_RVA + impBase
        ilt0RVA: Int = descRVA + 100
        ilt1RVA: Int = ilt0RVA + 8 * (nk + 1)
        ilt2RVA: Int = ilt1RVA + 8 * (nw + 1)
        ilt3RVA: Int = ilt2RVA + 8 * (nu + 1)
        dll0RVA: Int = ilt3RVA + 8 * (ng + 1)
        dll1RVA: Int = dll0RVA + 13             # "kernel32.dll\\0"
        dll2RVA: Int = dll1RVA + 11             # "ws2_32.dll\\0"
        dll3RVA: Int = dll2RVA + 11             # "user32.dll\\0"
        hint0RVA: Int = dll3RVA + 10            # "gdi32.dll\\0"
        put32(ilt0RVA); put32(0); put32(0); put32(dll0RVA); put32(DATA_RVA + IAT_IN_DATA)
        put32(ilt1RVA); put32(0); put32(0); put32(dll1RVA); put32(DATA_RVA + IAT_IN_DATA + 8 * nk)
        put32(ilt2RVA); put32(0); put32(0); put32(dll2RVA); put32(DATA_RVA + IAT_IN_DATA + 8 * (nk + nw))
        put32(ilt3RVA); put32(0); put32(0); put32(dll3RVA); put32(DATA_RVA + IAT_IN_DATA + 8 * (nk + nw + nu))
        put32(0); put32(0); put32(0); put32(0); put32(0)'''
assert old in s, "导入段头"; s = s.replace(old, new)

old = '''        # ILT0（kernel32，nk+1 槽，PE32+ 每槽 8 字节，高 32 位保持 0）
        w = 512 + textRaw + impBase + 60'''
new = '''        # ILT0（kernel32，nk+1 槽，PE32+ 每槽 8 字节，高 32 位保持 0）
        w = 512 + textRaw + impBase + 100'''
assert old in s, "ILT0"; s = s.replace(old, new)

old = '''        # DLL 名 ×2
        w = 512 + textRaw + (dll0RVA - RDATA_RVA)
        putStr("kernel32.dll"); put8(0)
        putStr("ws2_32.dll"); put8(0)'''
new = '''        # ILT2（user32，nu+1 槽）
        w = 512 + textRaw + (ilt2RVA - RDATA_RVA)
        j = 0
        while j < nu + 1 {
            if j < nu {
                put32at(w + 8 * j, hintRVA[nk + nw + j])
            } else {
                put32at(w + 8 * j, 0)
            }
            j = j + 1
        }
        # ILT3（gdi32，ng+1 槽）
        w = 512 + textRaw + (ilt3RVA - RDATA_RVA)
        j = 0
        while j < ng + 1 {
            if j < ng {
                put32at(w + 8 * j, hintRVA[nk + nw + nu + j])
            } else {
                put32at(w + 8 * j, 0)
            }
            j = j + 1
        }
        # DLL 名 ×4
        w = 512 + textRaw + (dll0RVA - RDATA_RVA)
        putStr("kernel32.dll"); put8(0)
        putStr("ws2_32.dll"); put8(0)
        putStr("user32.dll"); put8(0)
        putStr("gdi32.dll"); put8(0)'''
assert old in s, "DLL名"; s = s.replace(old, new)

# 2) calcImpSize：四 DLL
old = '''        impSize = 60 + 8 * (NIMP_KERNEL32 + 1) + 8 * (NIMPORT - NIMP_KERNEL32 + 1) + 13 + 11'''
new = '''        impSize = 100 + 8 * (NIMP_KERNEL32 + 1) + 8 * (NIMP_WS2 + 1) + 8 * (NIMP_USER32 + 1) + 8 * (NIMP_GDI32 + 1) + 13 + 11 + 11 + 10'''
assert old in s, "calcImpSize"; s = s.replace(old, new)

# 3) 数据目录 Import size 60 → 100
old = '''        put32(60)                             # Import size（2 个 DLL 描述符 + 全零终止 = 3×20）'''
new = '''        put32(100)                            # Import size（4 个 DLL 描述符 + 全零终止 = 5×20）'''
assert old in s, "Import size"; s = s.replace(old, new)

# 4) 常量：NIMPORT 更新 + 新增分组计数
m = re.search(r"^    NIMPORT: Int = \d+$", s, re.M)
assert m, "NIMPORT 行"
s = s[:m.start()] + "    NIMPORT: Int = 48" + s[m.end():]
m2 = re.search(r"^    NIMP_KERNEL32: Int = \d+$", s, re.M)
assert m2, "NIMP_KERNEL32"
s = s[:m2.end()] + """
    NIMP_WS2: Int = 12
    NIMP_USER32: Int = 8
    NIMP_GDI32: Int = 7""" + s[m2.end():]

# 5) inames 两处补 33..47
add_names = '''        inames[33] = "GetDC"
        inames[34] = "ReleaseDC"
        inames[35] = "GetSystemMetrics"
        inames[36] = "SetCursorPos"
        inames[37] = "mouse_event"
        inames[38] = "keybd_event"
        inames[39] = "VkKeyScanA"
        inames[40] = "GetCursorPos"
        inames[41] = "CreateCompatibleDC"
        inames[42] = "CreateCompatibleBitmap"
        inames[43] = "SelectObject"
        inames[44] = "BitBlt"
        inames[45] = "GetDIBits"
        inames[46] = "DeleteDC"
        inames[47] = "DeleteObject"
'''
c = s.count('        inames[32] = "WSAGetLastError"\n')
assert c == 2, f"inames[32] 出现 {c} 次（应为 2）"
s = s.replace('        inames[32] = "WSAGetLastError"\n', '        inames[32] = "WSAGetLastError"\n' + add_names)

open(p, "w", encoding="utf-8").write(s)
print("wkcc 四 DLL 导入表改造完成")
