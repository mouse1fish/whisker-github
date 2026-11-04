p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()

# 1) serve() 路由重构：AI 前缀代理 + 原生路由 → 网关白名单 + 全量反代
old1 = '''            body: Str = bodyStr(buf, headEnd, bodyNeed)
            # /api/ai/* → 反向代理到 Python AI 层（127.0.0.1:8001，内部 worker）
            if matchBytes(buf, pathStart(buf, 4096), "/api/ai") {
                upreq: Str = buildUpstream(reqMethodStr(buf), path, body)
                proxyRoundTrip(sock, upreq)
                netClose(sock)
                return
            }
            # POST /api/exec → 原生命令执行器（procSpawnPipe + strbuf 捕获，输出上限 64KB）
            if mPost and path == "/api/exec" {
                cmd: Str = jsonGetStr(body, "command")
                if strLen(cmd) == 0 {
                    sendAll(sock, respStr("400 Bad Request", "application/json", '{"error":"missing command"}'))
                } else {
                    sendAll(sock, respStr("200 OK", "application/json", execCapture(cmd)))
                }
                netClose(sock)
                return
            }
            if mGet {
                if path == "/" {
                    sendAll(sock, respStr("200 OK", "text/html; charset=utf-8", homePage()))
                } elif path == "/api/status" {
                    sendAll(sock, respStr("200 OK", "application/json", statusJson()))
                } elif path == "/api/time" {
                    sendAll(sock, respStr("200 OK", "application/json", timeJson()))
                } else {
                    sendAll(sock, respStr("404 Not Found", "application/json", '{"error":"not found"}'))
                }
            } elif mPost {
                if path == "/api/echo" {
                    sendAll(sock, respStr("200 OK", "text/plain; charset=utf-8", body))
                } else {
                    sendAll(sock, respStr("404 Not Found", "application/json", '{"error":"not found"}'))
                }
            } else {
                sendAll(sock, respStr("405 Method Not Allowed", "text/plain", "method not allowed"))
            }
            netClose(sock)'''
new1 = '''            body: Str = bodyStr(buf, headEnd, bodyNeed)
            # ==== 网关模式：原生路由白名单之外，全部反代到 Python 平台（:8001 内部）====
            native: Int = 0
            if mGet {
                if path == "/api/time" {
                    native = 1
                } elif path == "/native" {
                    native = 1
                } elif path == "/api/frontdoor" {
                    native = 1
                }
            } elif mPost {
                if path == "/api/echo" {
                    native = 1
                } elif path == "/api/exec" {
                    native = 1
                }
            }
            if native == 0 {
                upreq: Str = buildUpstream(reqMethodStr(buf), path, body)
                proxyRoundTrip(sock, upreq)
                netClose(sock)
                return
            }
            # ==== 原生路由 ====
            if mGet {
                if path == "/api/time" {
                    sendAll(sock, respStr("200 OK", "application/json", timeJson()))
                } elif path == "/native" {
                    sendAll(sock, respStr("200 OK", "text/html; charset=utf-8", nativePage()))
                } else {
                    sendAll(sock, respStr("200 OK", "application/json", frontdoorJson()))
                }
            } else {
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
            }
            netClose(sock)'''
if old1 in s:
    s = s.replace(old1, new1)
    print("路由重构 OK")
else:
    print("!! 路由块未匹配")

# 2) statusJson/homePage → frontdoorJson/nativePage（网关身份与页面）
old2 = '''    def statusJson -> Str {
        s: Str = '{"status":"ok","system":"EonOS","lang":"whisker","version":"0.2.0"'
        s = strCat(s, ',"uptime_ms":')
        s = strCat(s, intToStr(wallMs()))
        s = strCat(s, '}')
        return s
    }'''
new2 = '''    def frontdoorJson -> Str {
        s: Str = '{"frontdoor":"whisker","system":"EonOS","lang":"whisker","version":"0.2.0"'
        s = strCat(s, ',"mode":"gateway","uptime_ms":')
        s = strCat(s, intToStr(wallMs()))
        s = strCat(s, '}')
        return s
    }'''
if old2 in s:
    s = s.replace(old2, new2)
    print("frontdoorJson OK")
else:
    print("!! statusJson 未匹配")

old3 = '''    def homePage -> Str {
        s: Str = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>EonOS</title></head><body>'
        s = strCat(s, '<h1>EonOS 原生 HTTP 服务器</h1>')
        s = strCat(s, '<p>由 Whisker 语言与自研编译链路构建：零 C、零 LLVM、零链接器。</p>')
        s = strCat(s, '<ul><li><a href="/api/status">GET /api/status</a></li>')
        s = strCat(s, '<li><a href="/api/time">GET /api/time</a></li>')
        s = strCat(s, '<li>POST /api/echo</li></ul>')
        s = strCat(s, '</body></html>')
        return s
    }'''
new3 = '''    def nativePage -> Str {
        s: Str = '<!DOCTYPE html><html><head><meta charset="utf-8"><title>EonOS 前门</title></head><body>'
        s = strCat(s, '<h1>EonOS 原生前门（网关模式）</h1>')
        s = strCat(s, '<p>Whisker 原生进程是唯一对外监听者：静态路由直答，其余反代到内部平台。</p>')
        s = strCat(s, '<ul><li><a href="/">平台 UI（反代）</a></li>')
        s = strCat(s, '<li><a href="/api/frontdoor">GET /api/frontdoor</a></li>')
        s = strCat(s, '<li><a href="/api/time">GET /api/time</a></li>')
        s = strCat(s, '<li>POST /api/echo · POST /api/exec</li></ul>')
        s = strCat(s, '</body></html>')
        return s
    }'''
if old3 in s:
    s = s.replace(old3, new3)
    print("nativePage OK")
else:
    print("!! homePage 未匹配")

open(p, "w", encoding="utf-8").write(s)
