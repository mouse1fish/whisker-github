# 1) native README：vLLM 直连 + 配置 + 职责表更新
p = r"G:/trea-Eon-os/eonos/native/README.md"
s = open(p, encoding="utf-8").read()
old = '''      │    GET  /api/frontdoor · /api/time · /native
      │    POST /api/echo · POST /api/exec（命令执行器，procSpawnPipe，上限 64KB）'''
new = '''      │    GET  /api/frontdoor · /api/time · /native · /api/ai/models
      │    POST /api/echo · POST /api/exec（命令执行器，procSpawnPipe，上限 64KB）
      │    POST /api/ai/chat → Whisker 直连 vLLM（OpenAI 兼容协议，concatenated 原生客户端）'''
assert old in s
s = s.replace(old, new)
old2 = '''后端起法二选一：'''
new2 = '''**AI 聊天走原生 vLLM 直连**（不经任何我们自己的 Python 胶水）：
`eonos.conf` 配 `vllm_host` / `vllm_port`（默认 127.0.0.1:8002，可指向远端 GPU 机器）。
启动 vLLM：`vllm serve <模型> --port 8002`。客户端自动发现模型（/v1/models），
请求/响应全程 JSON（含 `\\uXXXX` 与代理对解码）。验收替身：`test/mock_vllm.py`。

后端（平台 UI 反代目标）起法二选一：'''
assert old2 in s
s = s.replace(old2, new2)
old3 = '''| AI 模型运行时（engine 推理） | 推理引擎属 Python 生态，非语言能力问题 | 换本地模型服务（ollama:11434 / llama.cpp:8080，均为 C/C++ HTTP 服务）→ Whisker 用 netConnect 直连，Python 归零 |'''
new3 = '''| ~~AI 模型运行时（engine 推理）~~ | **已退役**（2026-11-03）：聊天改由 Whisker 直连 vLLM | ✓ 完成——`/api/ai/chat` 原生实现，UI 聊天已切到该端点 |'''
assert old3 in s
s = s.replace(old3, new3)
old4 = '''**已完成的原生化**（每杀一次 Python，这张表就长一行）：
首页与静态资源 ✓（Whisker 读盘直发，实测杀掉 Python 照常 200）、/api/frontdoor ✓、
/api/exec 命令执行 ✓、/api/time ✓、/api/echo ✓、网关反代与 502 降级 ✓。'''
new4 = '''**已完成的原生化**（每杀一次 Python，这张表就长一行）：
首页与静态资源 ✓、**AI 聊天（直连 vLLM）✓**、/api/frontdoor ✓、/api/exec ✓、
/api/time ✓、/api/echo ✓、/api/ai/models ✓、网关反代与 502 降级 ✓。

> 现在用 AI 能力时，链路是：浏览器 → Whisker httpd → vLLM（现成模型服务）。
> **我们自己的 Python 代码已不在任何用户路径上**——剩余的 Python 只可能是"模型服务本身"（vLLM）。'''
assert old4 in s
s = s.replace(old4, new4)
open(p, "w", encoding="utf-8").write(s)
print("native README OK")

# 2) 交接文档 12 节追加
p2 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/交接文档-自举完成.md"
s2 = open(p2, encoding="utf-8").read()
anchor = """**事件总线结论（不做）**"""
add = """**vLLM 原生客户端（2026-11-03）**：httpd 用 netConnect 直连 vLLM（OpenAI 兼容协议）——
`/api/ai/chat`（自动 /v1/models 发现模型 → 构造 chat/completions → 解析 choices[0].message.content）、
`/api/ai/models` 中继；`eonos.conf` 配 vllm_host/vllm_port（可指向远端 GPU 机器）。
jsonGetStr 增 `\\uXXXX → UTF-8` 解码（含代理对）——mock 用 ensure_ascii 输出验收，🚀 还原正确。
E2E：models ✓、chat（中文+emoji）✓、mock 下线 502 ✓；UI 聊天已切 `/api/ai/chat`。
**我们自己的 Python 代码不再处于任何用户路径**（剩余 Python = vLLM 模型服务本身）。
坑：`def` 是保留关键字，不能作参数名（编译期报"表达式里出现意外的关键字"）。

**事件总线结论（不做）**"""
assert anchor in s2
s2 = s2.replace(anchor, add, 1)
open(p2, "w", encoding="utf-8").write(s2)
print("交接文档 OK")

# 3) 进度.md
p3 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/进度.md"
s3 = open(p3, encoding="utf-8").read()
s3 = s3.replace(
    "> 最后更新：2026-11-03（第二十一轮·**静态文件服务：首页脱离 Python**）",
    "> 最后更新：2026-11-03（第二十二轮·**vLLM 原生直连：AI 聊天脱离 Python**）")
s3 = s3.replace(
    "本轮：httpd 增静态文件服务（readBytes 读盘直发，`/` 与 `/ui/*` 原生，路径穿越防护实测）；",
    "本轮：httpd 增 vLLM 原生客户端（/api/ai/chat + /api/ai/models，eonos.conf 可配远端）；\nUI 聊天切原生端点；jsonGetStr 支持 \\uXXXX/代理对解码；mock_vllm.py 验收替身；\n上一轮：静态文件服务（readBytes 读盘直发，`/` 与 `/ui/*` 原生，路径穿越防护实测）；")
open(p3, "w", encoding="utf-8").write(s3)
print("进度.md OK")
