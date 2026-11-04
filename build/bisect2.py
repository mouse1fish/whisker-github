p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
s = s.replace(
    '''                    sendAll(sock, respStr("200 OK", "application/json", strCat("cmd=", cmd)))''',
    '''                    r: Str = execCapture(cmd)
                    sendAll(sock, respStr("200 OK", "application/json", strCat("raw=", r)))''')
open(p, "w", encoding="utf-8").write(s)
print("实验2：execCapture 平铺")
