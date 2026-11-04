import re
# 1) 修 and_ri → movsxd
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
old = """    a.label("rt_mx_ok")
    a.mov_r_rip(RAX, "g_pt")
    a.and_ri(RAX, 0xFFFFFFFF)
    f.close()"""
new = """    a.label("rt_mx_ok")
    a.mov_r_rip(RAX, "g_pt")
    a.movsxd_rax_eax()                      # 取低 32 位（POINT.x）
    f.close()"""
assert old in s, "rt_mx_ok"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("movsxd 修复 OK")

# 2) wkcc：数组扩容 + 常量占位（正则匹配当前值）+ 分发
p2 = r"tools/wkcc.wk"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace("    hintRVA: Int[40]\n    inames: Str[40]", "    hintRVA: Int[64]\n    inames: Str[64]")
m = re.search(r"^    OFF_PROC_FREE: Int = \d+$", s2, re.M)
assert m, "OFF_PROC_FREE 行"
add = """
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
    OFF_SCREENSHOT: Int = 0"""
s2 = s2[:m.end()] + add + s2[m.end():]
old3 = """                if name == "procFree" {
                    ePopArgs(nargs, 0)
                    eCallRt(OFF_PROC_FREE); lastTy = "Int"; return
                }"""
new3 = old3 + """
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
                }"""
assert old3 in s2, "procFree 分发"
s2 = s2.replace(old3, new3)
open(p2, "w", encoding="utf-8").write(s2)
print("wkcc 常量与分发 OK")
