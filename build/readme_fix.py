import re
p = "README.md"
s = open(p, encoding="utf-8").read()

# 1) 坏链接 → 绝对地址
s = s.replace("[EonOS 原生前门](../eonos/native/)（纯 Whisker 的 HTTP 服务器 + 命令执行器 + AI 反向代理）。",
              "[EonOS 系统](https://github.com/mouse1fish/eonos)（纯 Whisker 的 HTTP 网关 + 命令执行器 + agent 原语 + vLLM 直连）。")

# 2) 自举路线 section：整段重写为"已完成"
m = re.search(r"## 为什么编译器现在还是 Python 写的？——自举路线[\s\S]*?(?=\n## 当前状态)", s)
assert m, "自举路线段"
new_section = '''## 自举路线（已完成 ✅）

编译器的终极验收：**用 Whisker 写 Whisker 的编译器，产物与自身逐字节一致（fixpoint）**。

| 步骤 | 状态 |
|---|---|
| ① 语言能跑（前端 + 自研后端 + 运行时） | ✅ M0/M1 |
| ② 去掉 C / LLVM（自研编码器 + PE 写出器） | ✅ |
| ③ 语法定型（Python 味语句 + 括号层次 + 函数 + 控制流） | ✅ |
| ④~⑧ 基础设施 → 词法器 → 语法分析器逐字/逐字节比对 | ✅ 21 样本全一致 |
| ⑨ 自研后端（blob 嵌入 + PE 生成器）· 全语言代码发射 | ✅ |
| ⑩ **自举完成：`wkcc2.exe` 编译自身，产物逐字节一致；Python 版退役为应急引导** | ✅ **2026-10-28** |

之后持续加固（2026-11）：`and/or` 短路语义、`ptrToInt/intToPtr`、strbuf 标准库、
系统原语（TCP/进程/时钟）、agent 原语（截图/鼠标/键盘）、四 DLL 导入表、
帧动态对齐（根治嵌套调用栈未对齐）、**CLI 参数化**（`wkcc2 源.wk [输出.exe] [blob]`）。

> `whiskerc`（Python 前端）现仅作**应急引导链**保留：`wkcc2` 损坏时可重建，
> 日常构建零 Python（`tools/selfbuild.ps1` 一条命令）。

'''
s = s[:m.start()] + new_section + s[m.end():]

# 3) 当前状态段：重写
m2 = re.search(r"## 当前状态[\s\S]*$", s)
assert m2, "当前状态段"
s = s[:m2.start()] + '''## 当前状态

**自举完成（fixpoint 逐字节一致）+ 系统能力扩展**。

- **编译链路**：`whiskerc` 前端 → 自研 x86-64 编码器 → 自研 PE 写出器 → Windows 原生 exe；
  自举编译器 `wkcc2.exe`（Whisker 写成）日常构建零 Python。**无 C / C++ / LLVM / 链接器 / libc**。
- **并发**：24 工作线程池 + 全局自旋锁 + 事件唤醒；主线程等系统静止。
- **语言能力**：Actor + 消息、`def`、区间循环、数组（带边界检查）、`Ptr` 与内存原语、
  字符串内置、`and/or` 短路、指针 cast（`ptrToInt/intToPtr`）、`cmdline()`。
- **系统原语**：TCP socket（含回环绑定）/ 进程启动与管道捕获 / 墙钟与睡眠。
- **agent 原语**：截屏（GDI→BMP）/ 鼠标 / 键盘（虚拟键码）。
- **标准库**：`strbuf`（动态字符串，倍增扩容）。
- **工具链**：CLI 编译（`wkcc2 源.wk [输出.exe] [blob]`）、便携 SDK、`wk.ps1` 构建驱动。
- **验收**：`verify_cp` **21/21** · `verify_boot` **15/15**（自举侧语义，含缺陷固化用例）·
  `verify_sys` **3/3 ×双编译器**（系统原语）· `selfbuild.ps1` fixpoint 复验。
- **实测性能**：`fanout` 并行段 49ms（约 1.5× MSVC -O2 的等价 C）；调度 20 万消息级场景全绿。

**已知欠账**：`use`/include（现用 def 片段拼接）、`defer`、错误码约定（strerror 注册表）、
跨 actor 前向 spawn、keep-alive、静态文件 >256KB 流式（截屏另走 8MB 专用路由）。
详见 [`进度.md`](./进度.md) 断点与 [`交接文档-自举完成.md`](./交接文档-自举完成.md)（含设计宪法第 11 节）。
'''
open(p, "w", encoding="utf-8").write(s)
print("README 终检修复完成")
