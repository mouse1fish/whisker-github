p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
s = s.replace(
    '''            if mPost and path == "/api/exec" {
                cmd: Str = jsonGetStr(body, "command")''',
    '''            if mPost and path == "/api/exec" {
                print("[exec] branch hit")
                cmd: Str = jsonGetStr(body, "command")
                print("[exec] cmdlen=", strLen(cmd))''')
s = s.replace(
    '''                } else {
                    sendAll(sock, respStr("200 OK", "application/json", execCapture(cmd)))
                }''',
    '''                } else {
                    r: Str = execCapture(cmd)
                    print("[exec] captured len=", strLen(r))
                    sendAll(sock, respStr("200 OK", "application/json", r))
                    print("[exec] sent")
                }''')
open(p, "w", encoding="utf-8").write(s)
print("打点完成")
