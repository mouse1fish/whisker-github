p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
s = s.replace(
    '''                cmd: Str = jsonGetStr(body, "command")
                if strLen(cmd) == 0 {
                    sendAll(sock, respStr("400 Bad Request", "application/json", '{"error":"missing command"}'))
                } else {
                    sendAll(sock, respStr("200 OK", "application/json", execCapture(cmd)))
                }''',
    '''                cmd: Str = jsonGetStr(body, "command")
                if strLen(cmd) == 0 {
                    sendAll(sock, respStr("400 Bad Request", "application/json", '{"error":"missing command"}'))
                } else {
                    sendAll(sock, respStr("200 OK", "application/json", strCat("cmd=", cmd)))
                }''')
open(p, "w", encoding="utf-8").write(s)
print("实验1：去掉 execCapture")
