import re
# ============ 1) 教程.md：§7 扩展 + §13 路线图 + §1 SDK 名 ============
p = "教程.md"
s = open(p, encoding="utf-8").read()
old = '''典型组合——字符串构建与性能计时：'''
new = '''### 7.1 系统原语（TCP / 进程 / 时钟）

| 函数 | 说明 |
|------|------|
| `wallMs()` / `sleepMs(n)` | 系统墙钟毫秒 / 睡眠 n 毫秒 |
| `netInit()` | 初始化 Winsock（进程一次） |
| `netListen(port)` / `netListenLocal(port)` | 监听端口 / **仅回环**（敏感服务用这个） |
| `netAccept(ls)` | 阻塞等待连接 → 客户端 socket |
| `netConnect(host, port)` | 连接 IPv4 地址 |
| `netSend(s, buf, n)` / `netRecv(s, buf, n)` | 收发（recv 返回 0 = 对端关闭） |
| `netClose(s)` / `netErr()` | 关闭 / 最近错误码 |
| `procSpawn(cmd)` / `procSpawnPipe(cmd)` | 启动进程（继承控制台 / 捕获 stdout+stderr） |
| `procRead(p, buf, n)` | 读子进程输出（0 = EOF） |
| `procWait(p)` / `procFree(p)` | 等待退出码 / 释放句柄 |
| `cmdline()` | 本进程完整命令行（自定义 CLI 用） |

### 7.2 agent 原语（屏幕 / 鼠标 / 键盘）

| 函数 | 说明 |
|------|------|
| `screenW()` / `screenH()` | 屏幕宽 / 高 |
| `mouseX()` / `mouseY()` | 光标位置 |
| `mouseMove(x, y)` | 移动光标 |
| `mouseDown(btn)` / `mouseUp(btn)` | 按下/抬起（btn：1 左 2 右 3 中） |
| `keyDown(vk)` / `keyUp(vk)` | 虚拟键码按键 |
| `keyVk(ch)` | 字符 → 键码（低字节 VK，高字节 Shift 状态） |
| `screenshot(path)` | 抓屏写 BMP 文件（32bpp，返回字节数） |

### 7.3 指针 / 数值

| 函数 | 说明 |
|------|------|
| `ptrToInt(p)` / `intToPtr(i)` | 指针 ↔ 整数（身份变换，句柄与地址算术用） |
| `load64` / `store64` / `isNull(p)` | 64 位读写 / 空指针判断 |

### 7.4 命令行编译

自举编译器支持 CLI 直传参数：

```
wkcc2 <输入.wk> [输出.exe] [blob路径]
# 无参数时退回默认：build/lex_input.txt -> build/selfhost.exe
# SDK 的 whisker compile 就是对它的封装（blob 自动带上）
```

典型组合——字符串构建与性能计时：'''
assert old in s, "教程 7"; s = s.replace(old, new, 1)

# §13 路线图刷新
m = re.search(r"## 13\. 路线图[\s\S]*$", s)
assert m, "教程 13"
s = s[:m.start()] + '''## 13. 路线图

- **已达成**：自举收敛（产物逐字节一致）；`and/or` 短路；系统原语（TCP/进程/时钟）；
  agent 原语（截图/鼠标/键盘）；`ptrToInt/intToPtr`；strbuf 标准库；wkcc CLI 参数化
- **候选**（按痛点驱动）：`use`/include（替代 def 片段拼接）、`defer`（作用域退出清理）、
  错误约定（每模块 strerror 注册表）、haredoc 式文档工具
- **刻意不做**：泛型、GC、tagged union、隐式类型转换（见交接文档"设计宪法"第 11 节）

EonOS（系统侧）见 [github.com/mouse1fish/eonos](https://github.com/mouse1fish/eonos)。
'''
open(p, "w", encoding="utf-8").write(s)
print("教程 OK")

# ============ 2) README：SDK 行 + 构建命令 ============
p2 = "README.md"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace("- 📦 **便携 SDK**（解压任意目录即用）：见 [`sdk/whisker-sdk/`](./sdk/whisker-sdk/)，分发 zip 为 [`sdk/whisker-sdk-2026-10-28.zip`](./sdk/whisker-sdk-2026-10-28.zip)",
                "- 📦 **便携 SDK**（解压任意目录即用）：见 [`sdk/whisker-sdk/`](./sdk/whisker-sdk/)，分发 zip 为 [`sdk/whisker-sdk-2026-11-03.zip`](./sdk/whisker-sdk-2026-11-03.zip)")
s2 = s2.replace("日常构建用 `tools/selfbuild.ps1`（Windows 原生，无需 Python），`tools/selfbuild.sh` 等价（Git Bash）",
                "日常构建用 `tools/selfbuild.ps1`（Windows 原生，无需 Python）；\n  编译器已支持 CLI：`build\\wkcc2.exe 源.wk [输出.exe]`")
open(p2, "w", encoding="utf-8").write(s2)
print("README OK")

# ============ 3) SDK README：CLI + 新示例 + 压缩包名 ============
p3 = "sdk/whisker-sdk/README.md"
s3 = open(p3, encoding="utf-8").read()
s3 = s3.replace("├── examples/          示例源码（hello / syntax / elif / def / decl）",
                "├── examples/          示例源码（hello / syntax / elif / def / decl / builtins_demo）")
s3 = s3.replace("""```bash
# 编译（输出名可省略，默认与源文件同名 .exe）
whisker compile hello.wk
whisker compile hello.wk myapp.exe

# 编译产物是独立 exe，直接运行
./hello.exe""",
                """```bash
# 编译（输出名可省略，默认与源文件同名 .exe）
whisker compile hello.wk
whisker compile hello.wk myapp.exe

# 编译产物是独立 exe，直接运行
./hello.exe

# 也可是直接调用编译器（CLI）：
bin/wkcc2.exe hello.wk out.exe share/rt_blob.bin""")
s3 = s3.replace("# Whisker SDK", "# Whisker SDK（2026-11-03）")
open(p3, "w", encoding="utf-8").write(s3)
print("SDK README OK")

# ============ 4) 打包新 zip ============
import shutil, os
old_zip = "sdk/whisker-sdk-2026-10-28.zip"
new_base = "sdk/whisker-sdk-2026-11-03"
if os.path.exists(new_base + ".zip"):
    os.remove(new_base + ".zip")
shutil.make_archive(new_base, "zip", "sdk", "whisker-sdk")
print("新 SDK zip:", os.path.getsize(new_base + ".zip"), "字节")
