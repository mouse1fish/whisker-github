p = r"G:/trea-Eon-os/eonos/native/build.ps1"
s = open(p, encoding="utf-8").read()
open(p, "w", encoding="utf-8-sig").write(s)
print("BOM added")
