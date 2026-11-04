p = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/交接文档-自举完成.md"
s = open(p, encoding="utf-8").read()
anchor = "## 9. B 阶段交付：strbuf 标准库 + wk 构建驱动 + cast 内置（2026-11-02）"
add = """## 9. B 阶段交付：strbuf 标准库 + wk 构建驱动 + cast 内置（2026-11-02）

> 2026-11-02 追加：**帧动态对齐**（本节第 5 条）与 **netListenLocal**（第 10 节）。"""
s = s.replace(anchor, add)
s = s.rstrip() + """

## 10. 命令执行器 + 帧动态对齐（2026-11-02 续）

1. **POST /api/exec**（httpd.wk）：`jsonGetStr`（JSON 字符串字段提取，带转义）→
   `execCapture`（procSpawnPipe + strbuf 捕获，64KB 上限）→ `jsonEscape` 转义回 JSON。
   E2E：echo/ver 输出捕获与转义正确，缺 command 400，AI 层离线 502。
2. **strbuf 补 `sbAppendByte` / `sbAppendBytes`**（原始字节追加，chunk 捕获用）。
3. **`netListenLocal(port)`**（runtime 新原语 + 双侧编译器）：仅绑定 127.0.0.1——
   带 exec 能力的前门不再暴露局域网。httpd 已切换。
4. **帧动态对齐（重要，编译器+运行时深层修复）**：
   - 现象：httpd 的 exec 嵌套调用（sendAll 的参数里再调带参函数）→ CreateProcessA
     内 KERNELBASE AV。根因：wkcc 的 def 调用参数求值期间有奇数个 push 挂栈，
     嵌套调用以 rsp≡8 进入被调函数；旧帧序言的奇偶校验只对"入口 rsp≡8"正确。
   - 修复：所有帧序言在 sub 前插 `and rsp, -16`（运行时 Frame + wkcc
     parseHandler/parseFunc 双侧），sub 量改为 16 对齐（旧奇偶校验逻辑在动态对齐下
     反而制造未对齐，已废弃）。此后**任意嵌套深度的未对齐入口都被帧内重对齐吸收**。
   - 教训（再次验证）：**改 runtime 后必须 `extract_runtime.py` + `sync_const.py` +
     全链重建**——只重建 wkcc.exe 不重提 blob，自举侧用的还是旧机器码（本次
     proc_echo/net_echo 崩溃即此）。
5. 测试工具教训：PowerShell 向 curl 传 JSON 会把 `\"` 搅碎（curl exit=3 URL_MALFORMAT），
   **用 `--data "@body.json"` 文件方式**。body 样例：eonos/native/body1.json、body2.json。"""
open(p, "w", encoding="utf-8").write(s)
print("交接文档已更新")
