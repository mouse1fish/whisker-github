import re
p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()

# 1) 字段：入口/出口路径 + argv 状态（挂在 entryPos 字段附近）
old = '''    entryPos: Int = 0          # entry 代码在用户代码区内的偏移（所有 actor 之后发射）'''
new = '''    entryPos: Int = 0          # entry 代码在用户代码区内的偏移（所有 actor 之后发射）
    # ---- CLI（cmdline 原语，2026-11-03）----
    inPath: Str = "build/lex_input.txt"     # 输入 .wk（无参数时的默认值，向后兼容）
    outPath: Str = "build/selfhost.exe"     # 输出 exe（同上）
    argLine: Str = ""
    argPos: Int = 0'''
assert old in s, "字段"; s = s.replace(old, new)

# 2) parseCli / nextArg（挂在 main 之前）
old = '''    # ================= 入口 =================
    def main {
        setup()
        n: Int = loadSrc("build/lex_input.txt")'''
new = '''    # ================= CLI =================
    # 取下一个参数（支持双引号包裹；无更多参数返回 ""）
    def nextArg -> Str {
        n: Int = strLen(argLine)
        p: Ptr = strPtr(argLine)
        i: Int = argPos
        while i < n and load8(ptrAdd(p, i)) == 32 { i = i + 1 }
        buf: Ptr = alloc(1024)
        j: Int = 0
        q: Int = 0
        if i < n and load8(ptrAdd(p, i)) == 34 {
            q = 1
            i = i + 1
        }
        done: Int = 0
        while i < n and done == 0 {
            c: Int = load8(ptrAdd(p, i))
            if q == 1 {
                if c == 34 {
                    done = 1
                    i = i + 1
                } else {
                    store8(ptrAdd(buf, j), c)
                    j = j + 1
                    i = i + 1
                }
            } else {
                if c == 32 {
                    done = 1
                } else {
                    store8(ptrAdd(buf, j), c)
                    j = j + 1
                    i = i + 1
                }
            }
        }
        store8(ptrAdd(buf, j), 0)
        argPos = i
        return ptrToStr(buf)
    }

    # 用法: wkcc <输入.wk> [输出.exe]；无参数 = 旧默认（build/lex_input.txt -> build/selfhost.exe）
    def parseCli {
        argLine = cmdline()
        argPos = 0
        skipArg()                       # 程序名
        a1: Str = nextArg()
        if strLen(a1) > 0 {
            inPath = a1
            a2: Str = nextArg()
            if strLen(a2) > 0 {
                outPath = a2
            }
        }
        print("[wkcc] 编译 ", inPath, " -> ", outPath)
    }

    def skipArg {
        a0: Str = nextArg()
    }

    # ================= 入口 =================
    def main {
        setup()
        parseCli()
        n: Int = loadSrc(inPath)'''
assert old in s, "main 入口"; s = s.replace(old, new)

# 3) 输出路径
old = '''        wrote: Int = writeBytes("build/selfhost.exe", out, fileSize)
        print("selfhost.exe 写出 = ", wrote, " 字节")'''
new = '''        wrote: Int = writeBytes(outPath, out, fileSize)
        print(outPath, " 写出 = ", wrote, " 字节")'''
assert old in s, "writeBytes"; s = s.replace(old, new)

open(p, "w", encoding="utf-8").write(s)
print("wkcc CLI 接入完成")
