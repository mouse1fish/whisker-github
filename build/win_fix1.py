p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
old = '''    # rt_win_pump() -> 1 存活 / 0 收到 WM_QUIT
    a.label("rt_win_pump")
    f = Frame(a)'''
new = '''    # rt_win_pump() -> 1 存活 / 0 收到 WM_QUIT
    a.label("rt_win_pump")
    f = Frame(a, nextra=1)'''
assert old in s, "pump"; s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("pump nextra 修正")
