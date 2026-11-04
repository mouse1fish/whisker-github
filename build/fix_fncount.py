p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
old = """        fldCount = 0
        hCount = 0
        fnCount = 0
        actSize[actCount] = 48"""
new = """        fldCount = 0
        hCount = 0
        # 注意：fnCount 不在此重置——def 表是全局的（前向引用/resolveFnFx 在 EOF 统一解析），
        # 因此跨 actor 的 def 名必须全局唯一（与 Python 侧的 actor 内作用域不同，已知限制）
        actSize[actCount] = 48"""
if old in s:
    s = s.replace(old, new)
    print("fnCount 全局化完成")
else:
    print("!! 未匹配")
open(p, "w", encoding="utf-8").write(s)
