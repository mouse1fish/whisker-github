p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
old = '''    def parseCli {
        print("[cli] 1 entered")
        argLine = cmdline()
        print("[cli] 2 line=", argLine)
        argPos = 0
        a0: Str = nextArg()
        print("[cli] 3 prog=", a0)
        a1: Str = nextArg()
        print("[cli] 4 a1=[", a1, "]")'''
new = '''    def parseCli {
        argLine = cmdline()
        argPos = 0
        skipArg()                       # 程序名
        a1: Str = nextArg()'''
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("打点已清")
