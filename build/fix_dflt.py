p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
s = s.replace("def cfgGet[key: Str, def: Str] -> Str {", "def cfgGet[key: Str, dflt: Str] -> Str {")
s = s.replace("def cfgInt[key: Str, def: Int] -> Int {", "def cfgInt[key: Str, dflt: Int] -> Int {")
s = s.replace("if n < 0 { return def }", "if n < 0 { return dflt }")
s = s.replace("if strLen(v) == 0 { return def }", "if strLen(v) == 0 { return dflt }")
s = s.replace("        return def\n    }", "        return dflt\n    }")
open(p, "w", encoding="utf-8").write(s)
print("def 参数名已改 dflt")
