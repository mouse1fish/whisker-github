p = r"tools/selfbuild.ps1"
s = open(p, encoding="utf-8").read()
open(p, "w", encoding="utf-8-sig").write(s)
print("已加 BOM")
