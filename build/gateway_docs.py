# 1) eonos/native/README.md：架构改网关模式
p = r"G:/trea-Eon-os/eonos/native/README.md"
s = open(p, encoding="utf-8").read()
old = '''```
浏览器 / 客户端
      │
      ▼
:8000  httpd.exe（Whisker 原生前门，仅绑定 127.0.0.1）
      ├─ 原生路由：GET / · /api/status · /api/time · POST /api/exec · /api/echo
      ├─ POST /api/exec → 命令执行器（procSpawnPipe 捕获，输出上限 64KB）
      └─ /api/ai/* → 反向代理 → :8001 ai_server.py（Python，AI 推理层）
                                    └─ engine.chat / health（内部 worker，不对外）
```'''
new = '''```
浏览器 / 客户端
      │
      ▼
:8000  httpd.exe（Whisker 原生前门·网关模式，仅绑定 127.0.0.1 —— 唯一对外监听者）
      ├─ 原生路由（Whisker 直答）：
      │    GET  /api/frontdoor · /api/time · /native
      │    POST /api/echo · POST /api/exec（命令执行器，procSpawnPipe，上限 64KB）
      └─ 其余全部反代 → :8001 Python 平台（内部 worker，不对外）
                          平台 UI（/）· /api/status · /api/chat(AI) · /api/tools
                          · agent 能力（截图/鼠标/键盘）等全部平台路由
```

后端起法二选一：
- 全平台：`python -m eonos --host 127.0.0.1 --port 8001`（网关默认后端，UI+AI+工具）
- 精简 AI 层：`python -m eonos.ai_server`（只有 /api/ai/health 与 /api/ai/chat）

AI 层/平台离线时，网关对反代路径优雅降级 502 `{"error":"ai layer offline"}`。'''
s = s.replace(old, new)
s = s.replace(
    "启动顺序：先 `python -m eonos.ai_server`（:8001），再 `httpd.exe`（:8000）。\nAI 层离线时，前门对 /api/ai/* 优雅降级 502 `{\"error\":\"ai layer offline\"}`。",
    "启动顺序：先 Python 后端（:8001），再 `httpd.exe`（:8000）。")
open(p, "w", encoding="utf-8").write(s)
print("native README 网关化 OK")

# 2) 交接文档 12 节追加网关模式与事件总线结论
p2 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/交接文档-自举完成.md"
s2 = open(p2, encoding="utf-8").read()
anchor = """- 门面特性：**零 libc**（PE 由自有写出器生成，无 C 运行时）、**逐字节自举 fixpoint**、
  **默认回环绑定**（netListenLocal，exec 等敏感能力不暴露局域网）"""
add = anchor + """

**网关模式（2026-11-02 晚）**：httpd 升级为唯一对外监听者——
原生路由白名单（GET /api/frontdoor · /api/time · /native；POST /api/echo · /api/exec），
其余路径（平台 UI、/api/status、/api/chat、agent 能力）全部反代到 :8001 Python 平台。
E2E：原生 5 条 + 反代 /api/status（富状态）/api/chat（AI 回复）/（UI 13225 字节与直连一致）全通。

**事件总线结论（不做）**：Whisker 的 Actor 消息即事件系统（分派即消息、订阅即 ActorRef），
经典 pub/sub 在无函数指针/泛型下无法表达异构订阅者，且当前无消费者——按宪法第 4 条
（正确且简单）不建总线。真需要时以"表驱动 ActorRef + tag 路由"起步。"""
s2 = s2.replace(anchor, add)
open(p2, "w", encoding="utf-8").write(s2)
print("交接文档 OK")

# 3) 进度.md
p3 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/进度.md"
s3 = open(p3, encoding="utf-8").read()
s3 = s3.replace(
    "> 最后更新：2026-11-02（第十九轮·**命令执行器 + 帧动态对齐**）",
    "> 最后更新：2026-11-02（第二十轮·**网关模式：前门成为唯一对外监听者**）")
s3 = s3.replace(
    "下一步候选（按 EonOS 全 Whisker 化路线）：",
    "本轮：httpd 升级网关模式（原生白名单 + 其余反代 :8001 全平台），Python 彻底退居内部；\n事件总线经论证**不做**（Actor 消息即事件系统，无消费者）。\n下一步候选（按 EonOS 全 Whisker 化路线）：")
open(p3, "w", encoding="utf-8").write(s3)
print("进度.md OK")
