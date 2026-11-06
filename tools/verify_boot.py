#!/usr/bin/env python3
"""verify_boot.py — 自举侧回归测试（测 wkcc2.exe 自身语义，补 verify_cp 的盲区）

用法（必须从项目根目录）: python tools/verify_boot.py
对用例库逐一: wkcc2 编译（CLI 传参）→ 运行产物 → 比对期望输出。

2026-11-03 扩展：本 session 暴露过的 wkcc 缺陷全部固化为用例
（字符串字段初值、def 前向引用、跨 actor 消息、spawn 字段初始化、
 and/or 短路、指针 cast、字符串内置、局部数组）。
"""
import os
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

OUT = "build/boot_case.exe"

# 用例 -> 期望 stdout（None 表示只要求 exit=0）
CASES = {
    # ---- 原有用例 ----
    "tests/boot/min_q.wk": b"1\n",        # handler 内局部声明
    "tests/boot/min_s.wk": b"1\n",        # def 内 elif（首条件真）
    "tests/boot/min_a.wk": b"1\n",        # actor 字段 + handler
    "tests/boot/min_p.wk": b"11\n",       # elif 链（首条件真）
    "tests/boot/min_r.wk": b"11\n",       # elif 调用条件（首条件真）
    "tests/boot/min_t.wk": b"33\n",       # elif 调用条件（首条件假，else 命中）——elif 双吃鉴别用例
    "examples/hello.wk": "你好，Whisker！\n".encode("utf-8"),
    # ---- 2026-11-03 固化：session 内暴露过的缺陷 ----
    "tests/boot/boot_strfield.wk": b"HELLO-FIELD\n",   # 字符串字段初值（曾有裸 RVA bug）
    "tests/boot/boot_fwddef.wk": b"42\n",              # def 前向引用（曾有 fnCount 按 actor 重置 bug）
    "tests/boot/boot_send.wk": b"pong 42\n",           # 跨 actor 消息（.send 曾整段未实现）
    "tests/boot/boot_spawnfield.wk": b"port=47231\n",  # spawn 字段初始化（曾不初始化）
    "tests/boot/boot_sc.wk": b"sc ok\n",               # and/or 短路（曾是位运算，两边都求值）
    "tests/boot/boot_cast.wk": b"cast ok\n",           # ptrToInt/intToPtr
    "tests/boot/boot_str.wk": b"n=3 s=abc 7\n",        # 字符串内置
    "tests/boot/boot_arr.wk": b"0-9\n",                # 局部数组
    # ---- 2026-11-06 固化：Float 类型（IEEE 754 位模式 + SSE2）----
    "tests/boot/boot_float.wk":
        b"9\n5\n14\n35\n4\n12345\n314\n1\n10\n0\n3\n9\n",  # 算术+字面量+SSE2 编码坑回归锚
}

ERR_MARKERS = ["期望", "未定义", "数组越界", "read fail", "异常", "缺少"]


def run(exe, timeout=30):
    p = subprocess.run([exe], capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def compile_case(src):
    """wkcc2 CLI 编译：wkcc2 <src> <out>；返回 (ok, 说明)"""
    if os.path.exists(OUT):
        os.remove(OUT)
    try:
        p = subprocess.run(["build/wkcc2.exe", src, OUT],
                           capture_output=True, timeout=60)
    except subprocess.TimeoutExpired:
        return False, "编译超时"
    text = (p.stdout + p.stderr).decode("utf-8", errors="replace")
    if p.returncode != 0 or "写出 =" not in text:
        return False, "编译失败 exit=%d %s" % (p.returncode, text[:120])
    for m in ERR_MARKERS:
        if m in text:
            return False, "编译报错: %s" % text[:120]
    if not os.path.exists(OUT):
        return False, "未产出 %s" % OUT
    return True, ""


def main():
    if not os.path.exists("build/wkcc2.exe"):
        print("错误: build/wkcc2.exe 不存在，先跑应急链重建（见 tools/selfbuild.sh 头注释）")
        return 1
    passed = 0
    failed = []
    for src, want in CASES.items():
        if not os.path.exists(src):
            failed.append((src, "用例文件缺失"))
            continue
        ok, why = compile_case(src)
        if not ok:
            failed.append((src, why))
            continue
        try:
            code2, out2, _ = run(OUT)
        except subprocess.TimeoutExpired:
            failed.append((src, "运行超时"))
            continue
        if code2 != 0:
            failed.append((src, "运行崩溃 exit=0x%X" % (code2 & 0xFFFFFFFF)))
        elif want is not None and out2 != want:
            failed.append((src, "输出 %r != 期望 %r" % (out2, want)))
        else:
            passed += 1
    for src, msg in failed:
        print("FAIL %s: %s" % (src, msg))
    print("==== 自举侧验收（wkcc2 语义，CLI 编译）：{}/{} 通过 ====".format(passed, len(CASES)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
