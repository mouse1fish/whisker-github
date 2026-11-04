# 1) httpd.wk：白名单 + 分发 + shotBig
p = r"G:/trea-Eon-os/eonos/native/httpd.wk"
s = open(p, encoding="utf-8").read()
old = '''                } elif path == "/api/agent/status" {
                    native = 1
                } elif path == "/" {'''
new = '''                } elif path == "/api/agent/status" {
                    native = 1
                } elif path == "/api/shot.bmp" {
                    native = 1
                } elif path == "/" {'''
assert old in s, "白名单"; s = s.replace(old, new)
old = '''                } elif path == "/api/agent/status" {
                    agentStatus(sock)
                } elif path == "/" {'''
new = '''                } elif path == "/api/agent/status" {
                    agentStatus(sock)
                } elif path == "/api/shot.bmp" {
                    shotBig(sock)
                } elif path == "/" {'''
assert old in s, "分发"; s = s.replace(old, new)
old = '''    def agentStatus[sock: Int] {'''
new = '''    # 截屏大图专用路由（8MB 缓冲；通用静态服务上限 256KB，装不下全屏 BMP）
    def shotBig[sock: Int] {
        fbuf: Ptr = alloc(8388608)
        n: Int = readBytes("G:/trea-Eon-os/eonos/web/shot.bmp", fbuf, 8388608)
        if n < 0 {
            sendAll(sock, respStr("404 Not Found", "application/json", '{"error":"no shot"}'))
            return
        }
        h: Str = strCat("HTTP/1.1 200 OK\\r\\nContent-Type: image/bmp\\r\\nContent-Length: ", intToStr(n))
        h = strCat(h, "\\r\\nConnection: close\\r\\n\\r\\n")
        netSend(sock, strPtr(h), strLen(h))
        netSend(sock, fbuf, n)
    }

    def agentStatus[sock: Int] {'''
assert old in s, "shotBig"; s = s.replace(old, new, 1)
open(p, "w", encoding="utf-8").write(s)
print("httpd shotBig OK")

# 2) UI：截图命令附带 <img src="/api/shot.bmp">
p2 = r"G:/trea-Eon-os/eonos/web/index.html"
s2 = open(p2, encoding="utf-8").read()
old2 = "addMsg('ai',`Screenshot: ${r.width}x${r.height}${r.ocr_text?'\\nOCR: '+r.ocr_text.substring(0,200):''}`);"
new2 = "addMsg('ai',`Screenshot: ${r.width}x${r.height}<br><img src=\"/api/shot.bmp\" style=\"max-width:100%;margin-top:6px;border-radius:6px\">`);"
assert old2 in s2, "UI 截图行"
s2 = s2.replace(old2, new2)
open(p2, "w", encoding="utf-8").write(s2)
print("UI img OK")
