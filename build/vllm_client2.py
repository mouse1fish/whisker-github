import re
p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
steps = []

# 1) jsonGetStr \uXXXX → UTF-8
old = '''                } elif e == 47 {
                    sb = sbAppendByte(sb, 47)
                } else {
                    sb = sbAppendByte(sb, 63)
                }'''
new = '''                } elif e == 47 {
                    sb = sbAppendByte(sb, 47)
                } elif e == 117 {
                    cp: Int = hex4(bs, j + 1)
                    if cp >= 56320 and cp <= 57343 {
                        cp = 63
                    } elif cp >= 55296 and cp <= 56319 {
                        if load8(ptrAdd(bs, j + 5)) == 92 and load8(ptrAdd(bs, j + 6)) == 117 {
                            lo: Int = hex4(bs, j + 7)
                            if lo >= 56320 and lo <= 57343 {
                                cp = 65536 + (cp - 55296) * 1024 + (lo - 56320)
                                j = j + 6
                            } else {
                                cp = 63
                            }
                        } else {
                            cp = 63
                        }
                    }
                    sb = sbAppendCp(sb, cp)
                    j = j + 4
                } else {
                    sb = sbAppendByte(sb, 63)
                }'''
assert old in s, "1 转义块"; s = s.replace(old, new); steps.append(1)

# 2) 白名单 GET：加 /api/ai/models
old = '''                } elif path == "/api/frontdoor" {
                    native = 1
                } elif path == "/" {'''
new = '''                } elif path == "/api/frontdoor" {
                    native = 1
                } elif path == "/api/ai/models" {
                    native = 1
                } elif path == "/" {'''
assert old in s, "2 白名单GET"; s = s.replace(old, new); steps.append(2)

# 3) 白名单 POST：加 /api/ai/chat
old = '''                } elif path == "/api/exec" {
                    native = 1
                }
            }'''
new = '''                } elif path == "/api/exec" {
                    native = 1
                } elif path == "/api/ai/chat" {
                    native = 1
                }
            }'''
assert old in s, "3 白名单POST"; s = s.replace(old, new); steps.append(3)

# 4) 原生分发 GET：加 models 分支
old = '''                } elif path == "/api/frontdoor" {
                    sendAll(sock, respStr("200 OK", "application/json", frontdoorJson()))
                } elif path == "/" {'''
new = '''                } elif path == "/api/frontdoor" {
                    sendAll(sock, respStr("200 OK", "application/json", frontdoorJson()))
                } elif path == "/api/ai/models" {
                    vllmModelsRelay(sock)
                } elif path == "/" {'''
assert old in s, "4 分发GET"; s = s.replace(old, new); steps.append(4)

# 5) 原生分发 POST：加 chat 分支
old = '''            } else {
                if path == "/api/echo" {
                    sendAll(sock, respStr("200 OK", "text/plain; charset=utf-8", body))
                } else {
                    cmd: Str = jsonGetStr(body, "command")
                    if strLen(cmd) == 0 {
                        sendAll(sock, respStr("400 Bad Request", "application/json", '{"error":"missing command"}'))
                    } else {
                        sendAll(sock, respStr("200 OK", "application/json", execCapture(cmd)))
                    }
                }
            }'''
new = '''            } else {
                if path == "/api/echo" {
                    sendAll(sock, respStr("200 OK", "text/plain; charset=utf-8", body))
                } elif path == "/api/exec" {
                    cmd: Str = jsonGetStr(body, "command")
                    if strLen(cmd) == 0 {
                        sendAll(sock, respStr("400 Bad Request", "application/json", '{"error":"missing command"}'))
                    } else {
                        sendAll(sock, respStr("200 OK", "application/json", execCapture(cmd)))
                    }
                } else {
                    vllmChat(sock, body)
                }
            }'''
assert old in s, "5 分发POST"; s = s.replace(old, new); steps.append(5)

# 6) 助手群（hex4/sbAppendCp/readAll/httpRound/bodyOf/req 构造/discoverModel/modelsRelay/vllmChat/cfg*）
old = '''    # ---- 静态文件服务（Whisker 直接读盘发文件，零 Python）----'''
new = '''    # ---- 配置（eonos.conf 键值行；缺省用内置默认值）----
    def cfgGet[key: Str, def: Str] -> Str {
        fbuf: Ptr = alloc(4096)
        n: Int = readBytes("G:/trea-Eon-os/eonos/native/eonos.conf", fbuf, 4096)
        if n < 0 { return def }
        store8(ptrAdd(fbuf, n), 0)
        klen: Int = strLen(key)
        i: Int = 0
        while i < n {
            atStart: Int = 0
            if i == 0 {
                atStart = 1
            } elif load8(ptrAdd(fbuf, i - 1)) == 10 {
                atStart = 1
            }
            if atStart == 1 {
                if matchBytes(fbuf, i, key) {
                    if load8(ptrAdd(fbuf, i + klen)) == 61 {
                        sb: Ptr = sbNew()
                        j: Int = i + klen + 1
                        while j < n {
                            c: Int = load8(ptrAdd(fbuf, j))
                            if c == 10 or c == 13 {
                                j = n
                            } else {
                                sb = sbAppendByte(sb, c)
                                j = j + 1
                            }
                        }
                        return sbStr(sb)
                    }
                }
            }
            i = i + 1
        }
        return def
    }

    def cfgInt[key: Str, def: Int] -> Int {
        v: Str = cfgGet(key, "")
        if strLen(v) == 0 { return def }
        return strToInt(v)
    }

    # ---- vLLM 客户端（OpenAI 兼容 HTTP，Whisker 直连）----
    def hex4[p: Ptr, off: Int] -> Int {
        v: Int = 0
        i: Int = 0
        while i < 4 {
            c: Int = load8(ptrAdd(p, off + i))
            d: Int = 0
            if c >= 48 and c <= 57 {
                d = c - 48
            } elif c >= 97 and c <= 102 {
                d = c - 87
            } elif c >= 65 and c <= 70 {
                d = c - 55
            }
            v = v * 16 + d
            i = i + 1
        }
        return v
    }

    def sbAppendCp[sb: Ptr, cp: Int] -> Ptr {
        if cp < 128 {
            return sbAppendByte(sb, cp)
        } elif cp < 2048 {
            sb = sbAppendByte(sb, 192 + cp / 64)
            return sbAppendByte(sb, 128 + cp % 64)
        } elif cp < 65536 {
            sb = sbAppendByte(sb, 224 + cp / 4096)
            sb = sbAppendByte(sb, 128 + (cp / 64) % 64)
            return sbAppendByte(sb, 128 + cp % 64)
        } else {
            sb = sbAppendByte(sb, 240 + cp / 262144)
            sb = sbAppendByte(sb, 128 + (cp / 4096) % 64)
            sb = sbAppendByte(sb, 128 + (cp / 64) % 64)
            return sbAppendByte(sb, 128 + cp % 64)
        }
    }

    def readAll[sock: Int] -> Str {
        sb: Ptr = sbNew()
        rbuf: Ptr = alloc(8192)
        done: Int = 0
        while done == 0 {
            n: Int = netRecv(sock, rbuf, 8192)
            if n <= 0 {
                done = 1
            } else {
                sb = sbAppendBytes(sb, rbuf, n)
            }
        }
        return sbStr(sb)
    }

    def httpRound[host: Str, port: Int, req: Str] -> Str {
        s: Int = netConnect(host, port)
        if s < 0 { return "" }
        netSend(s, strPtr(req), strLen(req))
        r: Str = readAll(s)
        netClose(s)
        return r
    }

    def bodyOf[resp: Str] -> Str {
        e: Int = findHeadEnd(strPtr(resp), strLen(resp))
        if e < 0 { return "" }
        return tailFrom(resp, e)
    }

    def buildModelsReq[host: Str, port: Int] -> Str {
        r: Str = strCat("GET /v1/models HTTP/1.1\\r\\nHost: ", host)
        r = strCat(r, ":")
        r = strCat(r, intToStr(port))
        r = strCat(r, "\\r\\nConnection: close\\r\\n\\r\\n")
        return r
    }

    def buildChatReq[host: Str, port: Int, payload: Str] -> Str {
        r: Str = strCat("POST /v1/chat/completions HTTP/1.1\\r\\nHost: ", host)
        r = strCat(r, ":")
        r = strCat(r, intToStr(port))
        r = strCat(r, "\\r\\nContent-Type: application/json\\r\\nContent-Length: ")
        r = strCat(r, intToStr(strLen(payload)))
        r = strCat(r, "\\r\\nConnection: close\\r\\n\\r\\n")
        return strCat(r, payload)
    }

    def buildChatPayload[model: Str, msg: Str] -> Str {
        pl: Str = strCat("{\\"model\\":\\"", model)
        pl = strCat(pl, "\\",\\"messages\\":[{\\"role\\":\\"user\\",\\"content\\":\\"")
        pl = strCat(pl, jsonEscape(msg))
        pl = strCat(pl, "\\"}],\\"max_tokens\\":512,\\"temperature\\":0.7}")
        return pl
    }

    def discoverModel[host: Str, port: Int] -> Str {
        raw: Str = httpRound(host, port, buildModelsReq(host, port))
        if strLen(raw) == 0 { return "" }
        return jsonGetStr(bodyOf(raw), "id")
    }

    def vllmModelsRelay[sock: Int] {
        host: Str = cfgGet("vllm_host", "127.0.0.1")
        port: Int = cfgInt("vllm_port", 8002)
        raw: Str = httpRound(host, port, buildModelsReq(host, port))
        if strLen(raw) == 0 {
            sendAll(sock, respStr("502 Bad Gateway", "application/json", '{"error":"vllm offline"}'))
            return
        }
        sendAll(sock, respStr("200 OK", "application/json", bodyOf(raw)))
    }

    def vllmChat[sock: Int, body: Str] {
        msg: Str = jsonGetStr(body, "message")
        if strLen(msg) == 0 {
            sendAll(sock, respStr("400 Bad Request", "application/json", '{"error":"missing message"}'))
            return
        }
        host: Str = cfgGet("vllm_host", "127.0.0.1")
        port: Int = cfgInt("vllm_port", 8002)
        model: Str = jsonGetStr(body, "model")
        if strLen(model) == 0 {
            model = discoverModel(host, port)
        }
        if strLen(model) == 0 {
            sendAll(sock, respStr("502 Bad Gateway", "application/json", '{"error":"vllm offline or no model"}'))
            return
        }
        raw: Str = httpRound(host, port, buildChatReq(host, port, buildChatPayload(model, msg)))
        if strLen(raw) == 0 {
            sendAll(sock, respStr("502 Bad Gateway", "application/json", '{"error":"vllm offline"}'))
            return
        }
        reply: Str = jsonGetStr(bodyOf(raw), "content")
        if strLen(reply) == 0 {
            sendAll(sock, respStr("502 Bad Gateway", "application/json", '{"error":"no content from model"}'))
            return
        }
        res: Str = strCat('{"response":"', jsonEscape(reply))
        res = strCat(res, '","model":"')
        res = strCat(res, jsonEscape(model))
        res = strCat(res, '","backend":"vllm"}')
        sendAll(sock, respStr("200 OK", "application/json", res))
    }

    # ---- 静态文件服务（Whisker 直接读盘发文件，零 Python）----'''
assert old in s, "6 助手群锚点"; s = s.replace(old, new, 1); steps.append(6)

open(p, "w", encoding="utf-8").write(s)
print("全部替换完成:", steps)
