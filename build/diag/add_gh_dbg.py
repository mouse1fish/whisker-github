p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
s = s.replace(
    """        ghActor[ghCount] = actName[curActor]
        ghMsg[ghCount] = name
        ghTag[ghCount] = hCount
        ghCount = ghCount + 1""",
    """        ghActor[ghCount] = actName[curActor]
        ghMsg[ghCount] = name
        ghTag[ghCount] = hCount
        ghCount = ghCount + 1
        print("[gh] ", intToStr(ghCount - 1), " ", ghActor[ghCount - 1], ".", ghMsg[ghCount - 1], " tag=", intToStr(ghTag[ghCount - 1]))""")
s = s.replace(
    """    def findTag[an: Str, mn: Str] -> Int {
        gi: Int = 0""",
    """    def findTag[an: Str, mn: Str] -> Int {
        print("[findTag] ", an, " . ", mn)
        gi: Int = 0""")
open(p, "w", encoding="utf-8").write(s)
print("调试打印已加")
