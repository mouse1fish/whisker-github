# legacy —— 已停止维护的 C 对照后端

这里是 Whisker 的 **M0/M1 早期"C 引导后端"**：把 AST 落成 C，再借 MSVC 编译成 exe。
它在语言早期很有用——`tools/verify.py` 曾经拿它和自研 x64 后端逐字比对输出，证明自研后端语义正确（当时 11/11 完全一致）。

**现在停止维护了**，原因很直接：每加一个语法特性，两个后端都要改一遍，等于被另一种语言拖住速度。用户的要求是"不要别的语言拖慢"，而自研 x64 后端已经能独立完成"源码 → 原生 exe"的全流程。

保留在这里是为了**必要时可回退/对照**：

```
legacy/
  codegen_c.py               AST → C 代码生成
  build.bat                  MSVC + NuGet Windows SDK 编译封装（路径写死在文件顶部）
  runtime/
    whisker_runtime.h/.c     C 版 Actor 运行时（邮箱 + M:N 调度器 + 静止检测）
    whisker_selftest.c       C 版运行时自检
```

它只支持 **M1 第四轮之前**的语法（`on X[...]`、`var`/分号写法、`ActorRef<...>` 等旧写法），不认后来的
Python 味语句（换行结束、赋值即声明）、`def` 函数、`for` 循环等新特性。

如果要重新启用，需要：
1. 把文件搬回原位置（`whiskerc/`、`runtime/`、`tools/`）
2. 在 `whiskerc/codegen_c.py` 里补齐新语法的生成（参考 `codegen_x64.py` 的语义实现，两边规则必须一致）
3. 在 `whiskerc/cli.py` 里恢复 `--backend c` 选项

> 复现 C 版运行时自检（需要 MSVC）：
> ```
> legacy\build.bat /Fe:selftest.exe ..\legacy\runtime\whisker_selftest.c ..\legacy\runtime\whisker_runtime.c
> build\selftest.exe
> ```