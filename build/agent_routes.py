p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()

old = '''                } elif path == "/api/ai/models" {
                    native = 1
                } elif path == "/" {'''
new = '''                } elif path == "/api/ai/models" {
                    native = 1
                } elif path == "/api/agent/status" {
                    native = 1
                } elif path == "/" {'''
assert old in s, "白名单GET"; s = s.replace(old, new)

old = '''                } elif path == "/api/ai/chat" {
                    native = 1
                }
            }'''
new = '''                } elif path == "/api/ai/chat" {
                    native = 1
                } elif path == "/api/screenshot" {
                    native = 1
                } elif path == "/api/mouse" {
                    native = 1
                } elif path == "/api/command" {
                    native = 1
                } elif path == "/api/type" {
                    native = 1
                }
            }'''
assert old in s, "白名单POST"; s = s.replace(old, new)

old = '''                } elif path == "/api/ai/models" {
                    vllmModelsRelay(sock)
                } elif path == "/" {'''
new = '''                } elif path == "/api/ai/models" {
                    vllmModelsRelay(sock)
                } elif path == "/api/agent/status" {
                    agentStatus(sock)
                } elif path == "/" {'''
assert old in s, "分发GET"; s = s.replace(old, new)

old = '''                } else {
                    vllmChat(sock, body)
                }
            }'''
new = '''                } elif path == "/api/screenshot" {
                    agentShot(sock)
                } elif path == "/api/mouse" {
                    agentMouse(sock, body)
                } elif path == "/api/command" {
                    agentCommand(sock, body)
                } elif path == "/api/type" {
                    agentType(sock, body)
                } else {
                    vllmChat(sock, body)
                }
            }'''
assert old in s, "分发POST"; s = s.replace(old, new)

old = '''    # ---- vLLM 客户端（OpenAI 兼容 HTTP，Whisker 直连）----'''
new = '''    # ---- agent 路由（截图 / 鼠标 / 键盘 / 命令，全原生）----
    def agentStatus[sock: Int] {
        res: Str = strCat('{"screen_w":', intToStr(screenW()))
        res = strCat(res, ',"screen_h":')
        res = strCat(res, intToStr(screenH()))
        res = strCat(res, ',"mouse_x":')
        res = strCat(res, intToStr(mouseX()))
        res = strCat(res, ',"mouse_y":')
        res = strCat(res, intToStr(mouseY()))
        res = strCat(res, '}')
        sendAll(sock, respStr("200 OK", "application/json", res))
    }

    def agentShot[sock: Int] {
        n: Int = screenshot("G:/trea-Eon-os/eonos/web/shot.bmp")
        if n < 0 {
            sendAll(sock, respStr("500 Internal Server Error", "application/json", '{"error":"screenshot failed"}'))
            return
        }
        res: Str = strCat('{"width":', intToStr(screenW()))
        res = strCat(res, ',"height":')
        res = strCat(res, intToStr(screenH()))
        res = strCat(res, ',"bytes":')
        res = strCat(res, intToStr(n))
        res = strCat(res, ',"image":"/ui/shot.bmp","ocr_text":""}')
        sendAll(sock, respStr("200 OK", "application/json", res))
    }

    def agentMouse[sock: Int, body: Str] {
        act: Str = jsonGetStr(body, "action")
        x: Int = jsonNum(body, "x")
        y: Int = jsonNum(body, "y")
        btn: Int = 1
        bt: Str = jsonGetStr(body, "button")
        if bt == "right" {
            btn = 2
        } elif bt == "middle" {
            btn = 3
        }
        if act == "move" {
            mouseMove(x, y)
        } elif act == "down" {
            mouseDown(btn)
        } elif act == "up" {
            mouseUp(btn)
        } else {
            mouseMove(x, y)
            mouseDown(btn)
            mouseUp(btn)
        }
        sendAll(sock, respStr("200 OK", "application/json", '{"success":true}'))
    }

    def agentType[sock: Int, body: Str] {
        txt: Str = jsonGetStr(body, "text")
        n: Int = strLen(txt)
        i: Int = 0
        typed: Int = 0
        while i < n {
            c: Int = load8(ptrAdd(strPtr(txt), i))
            vk: Int = keyVk(c)
            sh: Int = vk / 256
            v: Int = vk % 256
            if v >= 1 and v <= 254 {
                if sh == 1 or sh == 3 {
                    keyDown(16)
                }
                keyDown(v)
                keyUp(v)
                if sh == 1 or sh == 3 {
                    keyUp(16)
                }
                typed = typed + 1
            }
            i = i + 1
        }
        res: Str = strCat('{"typed":', intToStr(typed))
        res = strCat(res, ',"total":')
        res = strCat(res, intToStr(n))
        res = strCat(res, '}')
        sendAll(sock, respStr("200 OK", "application/json", res))
    }

    def agentCommand[sock: Int, body: Str] {
        cmd: Str = jsonGetStr(body, "command")
        if strLen(cmd) == 0 {
            sendAll(sock, respStr("400 Bad Request", "application/json", '{"error":"missing command"}'))
            return
        }
        full: Str = execCapture(cmd)
        out: Str = jsonGetStr(full, "output")
        code: Int = jsonNum(full, "exit")
        res: Str = strCat('{"stdout":"', jsonEscape(out))
        res = strCat(res, '","stderr":"","exit":')
        res = strCat(res, intToStr(code))
        res = strCat(res, ',"duration":"native"}')
        sendAll(sock, respStr("200 OK", "application/json", res))
    }

    # ---- vLLM 客户端（OpenAI 兼容 HTTP，Whisker 直连）----'''
assert old in s, "agent 实现锚点"; s = s.replace(old, new, 1)

old = '''    # 字符串 → JSON 安全转义
    def jsonEscape[s: Str] -> Str {'''
new = '''    # JSON 数字字段（"key": 123）-> Int（非负整数）
    def jsonNum[body: Str, key: Str] -> Int {
        kp: Str = strCat("\\"", key)
        kp = strCat(kp, "\\":")
        bs: Ptr = strPtr(body)
        n: Int = strLen(body)
        klen: Int = strLen(kp)
        i: Int = 0
        found: Int = 0 - 1
        while i + klen <= n {
            if matchBytes(bs, i, kp) {
                found = i
                i = n
            } else {
                i = i + 1
            }
        }
        if found < 0 { return 0 }
        j: Int = found + klen
        v: Int = 0
        while j < n {
            c: Int = load8(ptrAdd(bs, j))
            if c == 32 {
                j = j + 1
            } elif c >= 48 and c <= 57 {
                v = v * 10 + (c - 48)
                j = j + 1
            } else {
                j = n
            }
        }
        return v
    }

    # 字符串 → JSON 安全转义
    def jsonEscape[s: Str] -> Str {'''
assert old in s, "jsonNum 锚点"; s = s.replace(old, new)

open(p, "w", encoding="utf-8").write(s)
print("agent 路由接入完成")