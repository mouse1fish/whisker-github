p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
s = s.replace('mGet: Int = reqMethod(buf, "GET")', 'mGet: Bool = reqMethod(buf, "GET")')
s = s.replace('mPost: Int = reqMethod(buf, "POST")', 'mPost: Bool = reqMethod(buf, "POST")')
s = s.replace("if mGet == 1 {", "if mGet {")
s = s.replace("} elif mPost == 1 {", "} elif mPost {")
open(p, "w", encoding="utf-8").write(s)
print("类型修正完成")
