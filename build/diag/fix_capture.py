p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
# tExpect 会消费 "["，因此捕获目标类型后只需一次 tAdvance 消费类型名
old1 = '''        if ty == "ActorRef" {
            tExpect("[")
            tAdvance()
            fref = pt(0)
            tAdvance()
            tExpect("]")
        }'''
new1 = '''        if ty == "ActorRef" {
            tExpect("[")
            fref = pt(0)
            tAdvance()
            tExpect("]")
        }'''
old2 = '''            if ty == "ActorRef" {
                tExpect("[")
                tAdvance()
                dref = pt(0)
                tAdvance()
                tExpect("]")
            }'''
new2 = '''            if ty == "ActorRef" {
                tExpect("[")
                dref = pt(0)
                tAdvance()
                tExpect("]")
            }'''
old3 = '''                    if pty == "ActorRef" {
                        tExpect("[")
                        tAdvance()
                        pRef = pt(0)
                        tAdvance()
                        tExpect("]")
                    }'''
new3 = '''                    if pty == "ActorRef" {
                        tExpect("[")
                        pRef = pt(0)
                        tAdvance()
                        tExpect("]")
                    }'''
for o, n, nm in ((old1, new1, "parseField"), (old2, new2, "parseDeclOrAssign"), (old3, new3, "parseParamsOpt")):
    if o in s:
        s = s.replace(o, n)
        print(f"{nm} 修正")
    else:
        print(f"!! {nm} 未匹配")
open(p, "w", encoding="utf-8").write(s)
