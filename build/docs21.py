# 交接文档追加
p = "交接文档-自举完成.md"
s = open(p, encoding="utf-8").read()
anchor = "**agent 原语（2026-11-03）**"
add = """**CLI 参数化 + 回归固化（2026-11-03 晚）**：
- `wkcc2 <输入.wk> [输出.exe] [blob路径]`（无参数退回旧默认路径，向后兼容）；
  新增 `cmdline()` 系统原语（GetCommandLineA），wk.ps1/selfbuild.ps1/SDK 启动器全部改为 CLI 直调
- **修复 wkcc 字符串字段初值**：INIT 块曾写裸 RVA（不可解引用）→ 改 RIP 相对 LEA
  （传参覆盖字段才没暴露；`tests/boot/boot_strfield.wk` 已固化）
- **verify_boot 7 → 15 例**：把本 session 暴露过的缺陷全部固化为永久回归
  （字符串字段初值 / def 前向引用 / 跨 actor 消息 / spawn 字段初始化 / and-or 短路 /
   ptrToInt-intToPtr / 字符串内置 / 局部数组），编译改用 CLI 传参
- SDK 刷新：新工具链 + `builtins_demo.wk` + 启动器一行直调（告别临时目录），
  新分发包 `sdk/whisker-sdk-2026-11-03.zip`

**agent 原语（2026-11-03）**"""
assert anchor in s
s = s.replace(anchor, add, 1)
open(p, "w", encoding="utf-8").write(s)
print("交接文档 OK")

# 进度.md
p2 = "进度.md"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace(
    "> 最后更新：2026-11-03（第二十三轮·**agent 原语：截图/鼠标/键盘全原生**）",
    "> 最后更新：2026-11-03（第二十四轮·**编译器 CLI 参数化 + 回归固化 + SDK 刷新**）")
s2 = s2.replace(
    "本轮：agent 原语落地",
    "本轮：wkcc CLI（源/输出/blob 三参，cmdline 原语）+ 字符串字段初值修复 +\nverify_boot 15 例（session 缺陷全固化）+ SDK/教程/README 刷新；\n上一轮：agent 原语落地")
open(p2, "w", encoding="utf-8").write(s2)
print("进度.md OK")
