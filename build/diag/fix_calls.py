p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
s = s.replace('d: Int = localSlot(vname, "Int", 0)', 'd: Int = localSlot(vname, "Int", 0, "")')
s = s.replace('dl: Int = localSlot(lname, "Int", 0)', 'dl: Int = localSlot(lname, "Int", 0, "")')
open(p, "w", encoding="utf-8").write(s)
print("已更新两处 Int 局部槽调用")
