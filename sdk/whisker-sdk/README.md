# Whisker SDK

Whisker 语言工具链的便携分发包。**解压到任何目录即可用**，不写注册表、不依赖环境变量、无需管理员权限。

## 包内容

```
whisker-sdk/
├── bin/wkcc2.exe      自举编译器（Whisker 语言写成，编译 .wk → Windows x64 exe）
├── share/rt_blob.bin  运行时机器码 blob（编译必需，编译器自动拼接进产物）
├── examples/          示例源码（hello / syntax / elif / def / decl）
├── whisker            POSIX sh 包装器（Git Bash / MSYS / Cygwin / WSL 调用）
└── whisker.cmd        Windows cmd 包装器
```

## 安装（任意系统/任意目录）

1. 把 `whisker-sdk/` 整个目录放到任何位置，例如 `C:\tools\whisker-sdk` 或 `D:\我的工具\whisker-sdk`（路径含中文和空格均可）
2.（可选）把 `bin` 的**上级目录**加入 PATH，即可在任意位置敲 `whisker`
3. 完成。卸载 = 删目录

## 使用

```bash
# 编译（输出名可省略，默认与源文件同名 .exe）
whisker compile hello.wk
whisker compile hello.wk myapp.exe

# 编译产物是独立 exe，直接运行
./hello.exe

# 查看版本
whisker version
```

不用包装器也可以手动编译（理解原理用）：

```bash
mkdir build
cp /path/to/sdk/share/rt_blob.bin build/rt_blob.bin
cp hello.wk build/lex_input.txt        # 编译器固定读这个路径
/path/to/sdk/bin/wkcc2.exe             # 在含 build/ 的目录里运行
cp build/selfhost.exe hello.exe        # 产物在这里
```

## 系统要求与已知边界（如实说明）

- **运行平台**：Windows x64（编译产物为 PE32+，运行时走 Win32 API）。
  在 Linux/macOS 上目前只能"阅读/分发"源码，无法编译运行——ELF/Mach-O 后端在路线图中
- **语言子集**：自举编译器当前可靠支持单入口 actor（Main）+ def 函数 + 字段 + 完整控制流
  （if/elif/else、while、for..in..区间、break/continue）+ 内置函数（print/strLen/strCat/
  intToStr/strToInt/strEq/alloc/copyBytes/readBytes/writeBytes/nowMs/ptrAdd/load8/store8/strPtr）
- **尚未接通**：跨 actor 消息传递（`spawn` 可解析、`.send` 已解析但未发射）。完整的
  Actor 消息语义目前由 Python 参考编译器（whiskerc）支持，自举侧在路线图中
- 编译器报错格式：`[wkcc] ...`，出现即编译失败（包装器会返回非零退出码）

## 从源码重建 SDK（应急链）

若 wkcc2.exe 损坏，用仓库里的 Python 引导编译器重建：

```bash
python -m whiskerc build tools/wkcc.wk       # 需要 Python 3 + 仓库完整源码
cp tools/wkcc.wk build/lex_input.txt
python tools/run_pe_test.py build/wkcc.exe
cp build/selfhost.exe build/wkcc2.exe        # 新的 wkcc2
cp build/wkcc2.exe /path/to/sdk/bin/         # 更新 SDK
```

详见仓库 `交接文档-自举完成.md`。
