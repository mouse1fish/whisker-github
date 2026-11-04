# 1) native README：架构 + Python 角色与退出路线
p = r"G:/trea-Eon-os/eonos/native/README.md"
s = open(p, encoding="utf-8").read()
old = ''':8000  httpd.exe（Whisker 原生前门·网关模式，仅绑定 127.0.0.1 —— 唯一对外监听者）
      ├─ 原生路由（Whisker 直答）：
      │    GET  /api/frontdoor · /api/time · /native
      │    POST /api/echo · POST /api/exec（命令执行器，procSpawnPipe，上限 64KB）
      └─ 其余全部反代 → :8001 Python 平台（内部 worker，不对外）
                          平台 UI（/）· /api/status · /api/chat(AI) · /api/tools
                          · agent 能力（截图/鼠标/键盘）等全部平台路由'''
new = ''':8000  httpd.exe（Whisker 原生前门·网关模式，仅绑定 127.0.0.1 —— 唯一对外监听者）
      ├─ 原生路由（Whisker 直答，Python 不参与）：
      │    GET  /                    → 读盘发首页（web/index.html）
      │    GET  /ui/*                → 静态文件（MIME 判断 + 路径穿越防护）
      │    GET  /api/frontdoor · /api/time · /native
      │    POST /api/echo · POST /api/exec（命令执行器，procSpawnPipe，上限 64KB）
      └─ 其余全部反代 → :8001 后端（内部 worker，不对外）
                          /api/status · /api/chat(AI) · /api/tools · agent 能力'''
assert old in s
s = s.replace(old, new)
s = s.replace("""| `std/strbuf_test.wk` | strbuf 验收用例 |""",
"""| `std/strbuf_test.wk` | strbuf 验收用例 |
| `../web/index.html` | 平台首页（静态，Whisker 读盘直发；旧 Python 生成页的快照） |""")
anchor = "## std 路线图（core / extended 分层）"
add = """## Python 的角色与退出路线（重要澄清）

**Whisker 编译器链零 Python**（自举 fixpoint 逐字节一致，日常构建仅用自举产物）。
EonOS 中 Python 仅剩两个职责，且**都有明确退出路径**：

| Python 现状职责 | 为什么现在还在 | 退出路径 |
|---|---|---|
| AI 模型运行时（engine 推理） | 推理引擎属 Python 生态，非语言能力问题 | 换本地模型服务（ollama:11434 / llama.cpp:8080，均为 C/C++ HTTP 服务）→ Whisker 用 netConnect 直连，Python 归零 |
| 桌面 agent（截图/鼠标/键盘） | 缺 Windows GDI/SendInput 原语 | extended std 原语补齐后原生实现 |

**已完成的原生化**（每杀一次 Python，这张表就长一行）：
首页与静态资源 ✓（Whisker 读盘直发，实测杀掉 Python 照常 200）、/api/frontdoor ✓、
/api/exec 命令执行 ✓、/api/time ✓、/api/echo ✓、网关反代与 502 降级 ✓。

## std 路线图（core / extended 分层）"""
s = s.replace(anchor, add)
open(p, "w", encoding="utf-8").write(s)
print("native README OK")

# 2) 交接文档 12 节追加
p2 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/交接文档-自举完成.md"
s2 = open(p2, encoding="utf-8").read()
anchor2 = """**事件总线结论（不做）**"""
add2 = """**静态文件服务（2026-11-03）**：httpd 用 readBytes 直接读盘发文件（`eonos/web/` 为 web 根），
`/` = web/index.html、`/ui/*` = 静态路由（MIME 判断 + `..` 路径穿越防护，实测 400 拦截）。
**首页从此不经过 Python**——实测仅启动 httpd（无 Python）时 `/` 仍 200 / 13225 字节。
Python 角色与退出路线见 `eonos/native/README.md`（剩模型运行时 + agent 两项，均有退出路径）。

**事件总线结论（不做）**"""
s2 = s2.replace(anchor2, add2, 1)
open(p2, "w", encoding="utf-8").write(s2)
print("交接文档 OK")

# 3) 进度.md
p3 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/进度.md"
s3 = open(p3, encoding="utf-8").read()
s3 = s3.replace(
    "> 最后更新：2026-11-02（第二十轮·**网关模式：前门成为唯一对外监听者**）",
    "> 最后更新：2026-11-03（第二十一轮·**静态文件服务：首页脱离 Python**）")
s3 = s3.replace(
    "本轮：httpd 升级网关模式（原生白名单 + 其余反代 :8001 全平台），Python 彻底退居内部；\n事件总线经论证**不做**（Actor 消息即事件系统，无消费者）。",
    "本轮：httpd 增静态文件服务（readBytes 读盘直发，`/` 与 `/ui/*` 原生，路径穿越防护实测）；\n实测**无 Python 时首页照常 200**；Python 退出路线成文（模型运行时→ollama/llama.cpp 直连；\nagent→extended std 原语）。")
open(p3, "w", encoding="utf-8").write(s3)
print("进度.md OK")
