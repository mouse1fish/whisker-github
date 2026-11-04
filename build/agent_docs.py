# 1) native README：agent 路由 + 原语表 + Python 职责表（agent 打勾退役）
p = r"G:/trea-Eon-os/eonos/native/README.md"
s = open(p, encoding="utf-8").read()
old = '''      │    GET  /api/frontdoor · /api/time · /native · /api/ai/models
      │    POST /api/echo · POST /api/exec（命令执行器，procSpawnPipe，上限 64KB）
      │    POST /api/ai/chat → Whisker 直连 vLLM（OpenAI 兼容协议，concatenated 原生客户端）'''
new = '''      │    GET  /api/frontdoor · /api/time · /native · /api/ai/models
      │         /api/agent/status（屏幕/光标）· /api/shot.bmp（截图大图 8MB 缓冲）
      │    POST /api/echo · POST /api/exec（命令执行器，procSpawnPipe，上限 64KB）
      │    POST /api/ai/chat → Whisker 直连 vLLM（OpenAI 兼容协议，原生客户端）
      │    POST /api/screenshot · /api/mouse · /api/type · /api/command（agent 原语，全原生）'''
assert old in s
s = s.replace(old, new)
old2 = "| 桌面 agent（截图/鼠标/键盘） | 缺 Windows GDI/SendInput 原语 | extended std 原语补齐后原生实现 |"
new2 = "| ~~桌面 agent（截图/鼠标/键盘）~~ | **已退役**（2026-11-03）：GDI/user32 原语落地 | ✓ 完成——screenshot/mouseMove/click/keyType 全原生（见下） |"
assert old2 in s
s = s.replace(old2, new2)
old3 = '''**已完成的原生化**（每杀一次 Python，这张表就长一行）：
首页与静态资源 ✓、**AI 聊天（直连 vLLM）✓**、/api/frontdoor ✓、/api/exec ✓、
/api/time ✓、/api/echo ✓、/api/ai/models ✓、网关反代与 502 降级 ✓。'''
new3 = '''**已完成的原生化**（每杀一次 Python，这张表就长一行）：
首页与静态资源 ✓、AI 聊天（直连 vLLM）✓、**agent（截图/鼠标/键盘）✓**、
/api/frontdoor ✓、/api/exec ✓、/api/command ✓、/api/time ✓、/api/echo ✓、
/api/ai/models ✓、/api/agent/status ✓、网关反代与 502 降级 ✓。

**agent 原语**（runtime user32.dll + gdi32.dll 导入，Whisker 内置）：
`screenW/screenH`（屏幕尺寸）、`mouseX/mouseY`（光标）、`mouseMove/mouseDown/mouseUp`（1 左 2 右 3 中）、
`keyDown/keyUp`（虚拟键码）、`keyVk`（字符→VK，高字节为 Shift 状态）、`screenshot(path)`（GDI 抓屏写 BMP）。
实测：截屏 7,285,530 字节 = 54 + 1707×1067×4 分毫不差；光标移动/复位、VK 映射、命令执行全通。'''
assert old3 in s
s = s.replace(old3, new3)
open(p, "w", encoding="utf-8").write(s)
print("native README OK")

# 2) 交接文档：agent 原语 + 容器溢出教训
p2 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/交接文档-自举完成.md"
s2 = open(p2, encoding="utf-8").read()
anchor = "**vLLM 原生客户端（2026-11-03）**"
add = """**agent 原语（2026-11-03）**：runtime 增 user32.dll + gdi32.dll 导入（15 个 API）→ 内置
screenW/screenH/mouseX/mouseY/mouseMove/mouseDown/mouseUp/keyDown/keyUp/keyVk/screenshot；
wkcc buildPe 的导入表从双 DLL 泛化为**四 DLL**（描述符 5×20、ILT×4、hint 表；inames/hintRVA 扩到 64）。
实测：截屏 7,285,530 字节（=54+1707×1067×4）、光标读取/移动、VK=321（'A'+Shift）、粘贴式命令全通。
**重要教训：wkcc 的 cbuf/rbuf 从 64KB 扩到 256KB**——wkcc 自身产物超过 64KB 后 cbuf 溢出，
踩坏紧邻的 rbuf 字符串池（症状：编译器打印乱码 + 写产物失败，但编译逻辑本身正确）。
**尺寸类容器一律按"文本窗口守卫 128KB → 产物 ≤180KB → 256KB 富余"配足，勿再拍 64KB。**

**vLLM 原生客户端（2026-11-03）**"""
assert anchor in s2
s2 = s2.replace(anchor, add, 1)
open(p2, "w", encoding="utf-8").write(s2)
print("交接文档 OK")

# 3) 进度.md
p3 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/进度.md"
s3 = open(p3, encoding="utf-8").read()
s3 = s3.replace(
    "> 最后更新：2026-11-03（第二十二轮·**vLLM 原生直连：AI 聊天脱离 Python**）",
    "> 最后更新：2026-11-03（第二十三轮·**agent 原语：截图/鼠标/键盘全原生**）")
s3 = s3.replace(
    "本轮：httpd 增 vLLM 原生客户端",
    "本轮：agent 原语落地（user32+gdi32，四 DLL 导入表，截屏/光标/键盘/命令全原生）；\nwkcc 容器溢出事故修复（cbuf/rbuf 64KB→256KB）；\n上一轮：httpd 增 vLLM 原生客户端")
open(p3, "w", encoding="utf-8").write(s3)
print("进度.md OK")
