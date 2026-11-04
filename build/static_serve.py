p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()

# 1) 白名单：加 / 与 /ui/ 前缀
old1 = '''            native: Int = 0
            if mGet {
                if path == "/api/time" {
                    native = 1
                } elif path == "/native" {
                    native = 1
                } elif path == "/api/frontdoor" {
                    native = 1
                }
            } elif mPost {'''
new1 = '''            native: Int = 0
            if mGet {
                if path == "/api/time" {
                    native = 1
                } elif path == "/native" {
                    native = 1
                } elif path == "/api/frontdoor" {
                    native = 1
                } elif path == "/" {
                    native = 1
                } elif matchBytes(buf, pathStart(buf, 4096), "/ui/") {
                    native = 1
                }
            } elif mPost {'''
assert old1 in s, "白名单块未匹配"
s = s.replace(old1, new1)

# 2) 原生 GET 分发：/ → 静态首页；其余（/ui/xxx）→ 静态文件
old2 = '''            if mGet {
                if path == "/api/time" {
                    sendAll(sock, respStr("200 OK", "application/json", timeJson()))
                } elif path == "/native" {
                    sendAll(sock, respStr("200 OK", "text/html; charset=utf-8", nativePage()))
                } else {
                    sendAll(sock, respStr("200 OK", "application/json", frontdoorJson()))
                }
            } else {'''
new2 = '''            if mGet {
                if path == "/api/time" {
                    sendAll(sock, respStr("200 OK", "application/json", timeJson()))
                } elif path == "/native" {
                    sendAll(sock, respStr("200 OK", "text/html; charset=utf-8", nativePage()))
                } elif path == "/api/frontdoor" {
                    sendAll(sock, respStr("200 OK", "application/json", frontdoorJson()))
                } elif path == "/" {
                    serveFile(sock, "index.html", "text/html; charset=utf-8")
                } else {
                    rel: Str = tailFrom(path, 4)
                    if hasDotDot(rel) {
                        sendAll(sock, respStr("400 Bad Request", "application/json", '{"error":"bad path"}'))
                    } else {
                        serveFile(sock, rel, mimeOf(rel))
                    }
                }
            } else {'''
assert old2 in s, "原生分发块未匹配"
s = s.replace(old2, new2)

# 3) 静态文件助手（挂在响应区之前）
old3 = '''    # ---- 响应 ----'''
new3 = '''    # ---- 静态文件服务（Whisker 直接读盘发文件，零 Python）----

    def endsWith[s: Str, suf: Str] -> Bool {
        n: Int = strLen(s)
        m: Int = strLen(suf)
        if m > n { return False }
        return matchBytes(strPtr(s), n - m, suf)
    }

    def tailFrom[s: Str, off: Int] -> Str {
        sb: Ptr = sbNew()
        n: Int = strLen(s)
        i: Int = off
        while i < n {
            sb = sbAppendByte(sb, load8(ptrAdd(strPtr(s), i)))
            i = i + 1
        }
        return sbStr(sb)
    }

    def hasDotDot[s: Str] -> Bool {
        n: Int = strLen(s)
        pp: Ptr = strPtr(s)
        i: Int = 0
        while i + 1 < n {
            if load8(ptrAdd(pp, i)) == 46 {
                if load8(ptrAdd(pp, i + 1)) == 46 {
                    return True
                }
            }
            i = i + 1
        }
        return False
    }

    def mimeOf[f: Str] -> Str {
        if endsWith(f, ".html") { return "text/html; charset=utf-8" }
        if endsWith(f, ".css") { return "text/css" }
        if endsWith(f, ".js") { return "application/javascript" }
        if endsWith(f, ".json") { return "application/json" }
        if endsWith(f, ".png") { return "image/png" }
        if endsWith(f, ".svg") { return "image/svg+xml" }
        if endsWith(f, ".ico") { return "image/x-icon" }
        return "application/octet-stream"
    }

    # 读盘发文件（web 根：G:/trea-Eon-os/eonos/web/）
    def serveFile[sock: Int, rel: Str, ctype: Str] -> Int {
        full: Str = strCat("G:/trea-Eon-os/eonos/web/", rel)
        fbuf: Ptr = alloc(262144)
        n: Int = readBytes(full, fbuf, 262144)
        if n < 0 {
            sendAll(sock, respStr("404 Not Found", "application/json", '{"error":"file not found"}'))
            return 0 - 1
        }
        h: Str = strCat("HTTP/1.1 200 OK\\r\\nContent-Type: ", ctype)
        h = strCat(h, "\\r\\nContent-Length: ")
        h = strCat(h, intToStr(n))
        h = strCat(h, "\\r\\nConnection: close\\r\\n\\r\\n")
        netSend(sock, strPtr(h), strLen(h))
        return netSend(sock, fbuf, n)
    }

    # ---- 响应 ----'''
assert old3 in s, "响应区锚点未匹配"
s = s.replace(old3, new3, 1)

open(p, "w", encoding="utf-8").write(s)
print("静态文件服务接入完成")
