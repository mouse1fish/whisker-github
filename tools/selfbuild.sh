#!/usr/bin/env bash
# Whisker 自举构建脚本（无 Python 参与）
#
# 用法（必须从项目根目录运行）:
#   bash tools/selfbuild.sh          # 自举构建 wkcc.wk 本身（收敛校验）
#   bash tools/selfbuild.sh 目标.wk  # 用 wkcc2 编译任意 Whisker 源文件
#
# 前置条件: build/wkcc2.exe 存在（自举链已建立）
# 若 wkcc2 损坏，用应急链重建:
#   python -m whiskerc build tools/wkcc.wk   # → build/wkcc.exe
#   cp tools/wkcc.wk build/lex_input.txt
#   python tools/run_pe_test.py build/wkcc.exe && cp build/selfhost.exe build/wkcc2.exe
set -e
cd "$(dirname "$0")/.."

WKC2=build/wkcc2.exe
if [ ! -f "$WKC2" ]; then
    echo "[selfbuild] 错误: $WKC2 不存在，请先用应急链重建（见脚本头注释）" >&2
    exit 1
fi

if [ $# -ge 1 ]; then
    # ---- 普通构建: wkcc2 编译用户目标 ----
    cp "$1" build/lex_input.txt
    ./"$WKC2" || { echo "[selfbuild] 编译失败: $1" >&2; exit 1; }
    echo "[selfbuild] OK: $1 -> build/selfhost.exe"
    exit 0
fi

# ---- 自举构建: wkcc2 编译 wkcc.wk 自身 ----
cp tools/wkcc.wk build/lex_input.txt
./"$WKC2" || { echo "[selfbuild] 自举编译失败" >&2; exit 1; }

if cmp -s "$WKC2" build/selfhost.exe; then
    echo "[selfbuild] 自举收敛确认: 产物与 wkcc2.exe 逐字节一致 (fixpoint)"
else
    # 理论上不应发生；若发生则再迭代一次
    echo "[selfbuild] 警告: 产物与 wkcc2.exe 不一致，再迭代一轮..." >&2
    cp build/selfhost.exe "$WKC2"
    cp tools/wkcc.wk build/lex_input.txt
    ./"$WKC2"
    cmp -s "$WKC2" build/selfhost.exe \
        && echo "[selfbuild] 第二轮收敛" \
        || { echo "[selfbuild] 错误: 两轮后仍未收敛，wkcc2 可能有 bug" >&2; exit 1; }
fi

# ---- 冒烟测试: hello 闭环 ----
cp examples/hello.wk build/lex_input.txt
./"$WKC2"
if ./build/selfhost.exe | grep -q "Whisker"; then
    echo "[selfbuild] 冒烟测试通过: hello 输出正常"
else
    echo "[selfbuild] 错误: hello 冒烟测试失败" >&2
    exit 1
fi
