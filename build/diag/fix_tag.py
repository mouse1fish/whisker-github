p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
# 1) 去掉两处调试打印
s = s.replace('''        ghCount = ghCount + 1
        print("[gh] ", intToStr(ghCount - 1), " ", ghActor[ghCount - 1], ".", ghMsg[ghCount - 1], " tag=", intToStr(ghTag[ghCount - 1]))''',
              "        ghCount = ghCount + 1")
s = s.replace('''    def findTag[an: Str, mn: Str] -> Int {
        print("[findTag] ", an, " . ", mn)
        gi: Int = 0''',
              '''    def findTag[an: Str, mn: Str] -> Int {
        gi: Int = 0''')
# 2) send 处改为占位 + 登记
s = s.replace('''                # 写 tag
                sTag: Int = findTag(sref, msg)
                if sTag < 0 {
                    err(strCat(strCat(sref, " 没有消息 "), msg))
                }
                e8(72); e8(199); e8(0)          # mov qword [rax], imm32（48 C7 00）
                e32(sTag)''',
              '''                # 写 tag（tag 依赖全量 handler 表；跨 actor 前向引用 → 占位后回填）
                e8(72); e8(199); e8(0)          # mov qword [rax], imm32（48 C7 00）
                sndSite[sndCount] = cw
                sndRef[sndCount] = sref
                sndMsg[sndCount] = msg
                sndCount = sndCount + 1
                e32(0)''')
# 3) 声明占位数组（挂在 ghCount 声明后）
s = s.replace('''    ghCount: Int = 0
''', '''    ghCount: Int = 0
    sndSite: Int[1024]     # send 的 tag 占位点（imm32 位置），解析完所有 actor 后回填
    sndRef: Str[1024]      # send 目标 actor 名
    sndMsg: Str[1024]      # send 消息名
    sndCount: Int = 0
''')
# 4) resolveSndTags（挂在 findTag 后面）
s = s.replace('''    def findTag[an: Str, mn: Str] -> Int {
        gi: Int = 0
        while gi < ghCount {
            if ghActor[gi] == an and ghMsg[gi] == mn {
                return ghTag[gi]
            }
            gi = gi + 1
        }
        return 0 - 1
    }''', '''    def findTag[an: Str, mn: Str] -> Int {
        gi: Int = 0
        while gi < ghCount {
            if ghActor[gi] == an and ghMsg[gi] == mn {
                return ghTag[gi]
            }
            gi = gi + 1
        }
        return 0 - 1
    }

    # 回填所有 send 的 tag（必须在所有 actor 解析完后调用）
    def resolveSndTags {
        si: Int = 0
        while si < sndCount {
            sTag: Int = findTag(sndRef[si], sndMsg[si])
            if sTag < 0 {
                err(strCat(strCat(sndRef[si], " 没有消息 "), sndMsg[si]))
            }
            u: Int = sTag
            if u < 0 { u = u + 4294967296 }
            store8(ptrAdd(cbuf, sndSite[si]), u % 256)
            store8(ptrAdd(cbuf, sndSite[si] + 1), (u / 256) % 256)
            store8(ptrAdd(cbuf, sndSite[si] + 2), (u / 65536) % 256)
            store8(ptrAdd(cbuf, sndSite[si] + 3), (u / 16777216) % 256)
            si = si + 1
        }
    }''')
# 5) Main 流程挂上 resolveSndTags
s = s.replace('''        lex()
        parseProgram()
        resolveFx()
        resolveFnFx()''', '''        lex()
        parseProgram()
        resolveFx()
        resolveFnFx()
        resolveSndTags()''')
open(p, "w", encoding="utf-8").write(s)
print("tag 回填机制完成")
