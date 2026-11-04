# Whisker 自举编译器 - 项目长期笔记

## 当前状态（2026-10-28）：自举 fixpoint 已达成
- 三步链全通：Python 编译器 → wkcc.exe → wkcc2.exe；wkcc2 编译 wkcc.wk 自身零报错，产物与 wkcc2 逐字节一致（cmp 通过）
- hello 闭环：wkcc2 编译 examples/hello.wk → "你好，Whisker！" exit=0
- verify_cp 21/21 无回归

## 已修复的历史根因（勿回退）
1. fnCount 翻倍：parseFunc 末尾多余 fnCount+1（已删，登记块统一递增）
2. 帧大小写死 4104：curSubSite + patchFrameSize() 回填（parseHandler/parseFunc 两处）
3. imm32 截断：parsePrimary 对 >2^31-1 用 movabs rax, imm64（字节提取只用 ≤256 常量链）
4. **elif 双 tAdvance**：parseIf 的 elif 递归前不可再 tAdvance()，入口统一吃关键字。此 bug 使 elif 条件退化为 "( 实参 )" 括号表达式（恒真/恒假），verify_cp 测不到（测的是 whiskerc 不是 wkcc.wk 的 parseIf）
5. [tok] dump 越界：需 if i4 >= count break

## 关键约定
- **日常构建零 Python**：`bash tools/selfbuild.sh`（自举+收敛校验+冒烟）或 `bash tools/selfbuild.sh 目标.wk`；exe 可直接从 shell 运行。Python 编译器（`python -m whiskerc build tools/wkcc.wk`）仅作应急引导链
- **回归双轨**：verify_cp（21/21，测 Python 前端）+ verify_boot（7/7，测 wkcc2 语义）——改 wkcc.wk 后两个都跑
- 测试必须从项目根目录跑（相对路径 build/rt_blob.bin、build/lex_input.txt）
- wkcc.wk 的 Main 读 build/lex_input.txt、写 build/selfhost.exe；自举产物替换用 cp selfhost.exe wkcc2.exe
- 调试工具：dbg_probe.py（int3 探针）、xdis.py（capstone 反汇编，勿命名 dis.py）、find_callers.py、verify_boot.py
- "无报错+语义正确"可能是假阴性（elif 恒真被 then 分支屏蔽）；鉴别需首条件为假的用例（min_t）
- 交接文档：交接文档-自举完成.md（终版，接手只读这份即可）
- **对外分发**：教程.md + sdk/whisker-sdk/（便携包，wrapper 在 %TEMP% 隔离 build 目录适配 wkcc2 的硬编码路径）；备份在 backups/（make_archive 必须项目外生成再移入，否则自包含递归膨胀）
- **能力边界（写文档/教程时如实标注）**：自举版 = 单 Main actor + def/字段/全控制流 + 14 内置；.send 已解析未发射；完整 actor 语义在 Python 编译器；"首次赋值即声明"自举版不支持

## 待办（维护与扩展路线，详见交接文档第 5 节）
- 近期：自举侧接通 .send 发射、错误恢复（tExpect 同步点）
- 中期：64 位比较/大立即数完善、数组/字符串标准库上移
- 远期：ELF/Mach-O 后端、selfbuild 应急链固化为 tools/boot.sh
