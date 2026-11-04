p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
s = s.replace(
    '''                    r: Str = execCapture(cmd)
                    sendAll(sock, respStr("200 OK", "application/json", strCat("raw=", r)))''',
    '''                    sendAll(sock, respStr("200 OK", "application/json", execCapture(cmd)))''')
open(p, "w", encoding="utf-8").write(s)
print("httpd 已恢复嵌套写法")
