p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
# 1) localSlot 恢复 3 参，改读 pendingRef
s = s.replace(
    "def localSlot[name: Str, ty: Str, arrN: Int, refTy: Str] -> Int {",
    "def localSlot[name: Str, ty: Str, arrN: Int] -> Int {")
s = s.replace(
    "        localRef[localCount] = refTy\n        localCount = localCount + 1",
    "        localRef[localCount] = pendingRef\n        pendingRef = \"\"\n        localCount = localCount + 1")
# 2) 三个调用点改为先设 pendingRef
s = s.replace("localSlot(pname, pty, pArrN)", "pendingRef = pRef\n                    localSlot(pname, pty, pArrN)")
s = s.replace("d: Int = localSlot(name, ty, arrN, dref)", "pendingRef = dref\n            d: Int = localSlot(name, ty, arrN)")
s = s.replace('d: Int = localSlot(vname, "Int", 0, "")', 'pendingRef = ""\n            d: Int = localSlot(vname, "Int", 0)')
s = s.replace('dl: Int = localSlot(lname, "Int", 0, "")', 'pendingRef = ""\n            dl: Int = localSlot(lname, "Int", 0)')
# 3) 声明 pendingRef 字段（加在 lastRefTy 旁）
s = s.replace(
    'lastRefTy: Str = ""     # 最近一次 ActorRef 表达式的目标 actor 名（send 的 tag 解析用）',
    'lastRefTy: Str = ""     # 最近一次 ActorRef 表达式的目标 actor 名（send 的 tag 解析用）\n    pendingRef: Str = ""    # localSlot 调用前设置：ActorRef 局部/参数的目标类型（def 最多 3 参的绕行）')
open(p, "w", encoding="utf-8").write(s)
print("localSlot 改为 pendingRef 模式完成")
