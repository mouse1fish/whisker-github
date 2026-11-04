p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
s = s.replace('''                print("[exec] branch hit")
                cmd: Str = jsonGetStr(body, "command")
                print("[exec] cmdlen=", strLen(cmd))''',
              '''                cmd: Str = jsonGetStr(body, "command")''')
s = s.replace('''                    r: Str = execCapture(cmd)
                    print("[exec] captured len=", strLen(r))
                    sendAll(sock, respStr("200 OK", "application/json", r))
                    print("[exec] sent")''',
              '''                    sendAll(sock, respStr("200 OK", "application/json", execCapture(cmd)))''')
open(p, "w", encoding="utf-8").write(s)
print("打点已清")
