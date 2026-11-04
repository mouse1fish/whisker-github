p = r"G:/trea-Eon-os/eonos/web/index.html"
s = open(p, encoding="utf-8").read()
n = s.count("api('/api/chat'")
s = s.replace("api('/api/chat'", "api('/api/ai/chat'")
open(p, "w", encoding="utf-8").write(s)
print(f"UI 聊天端点改写 {n} 处")
