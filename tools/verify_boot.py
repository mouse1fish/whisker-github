#!/usr/bin/env python3
"""verify_boot.py — 自举侧回归测试（测 wkcc2.exe 自身语义，补 verify_cp 的盲区）

用法（必须从项目根目录）: python tools/verify_boot.py
对 build/min_*.wk 用例库逐一: wkcc2 编译 → 运行产物 → 比对期望输出。
"""
import glob
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)

# 用例 -> 期望 stdout（None 表示只要求 exit=0）
CASES = {
    "tests/boot/min_q.wk": b"1\n",        # handler 内局部声明
    "tests/boot/min_s.wk": b"1\n",        # def 内 elif（首条件真）
    "tests/boot/min_a.wk": b"1\n",        # actor 字段 + handler
    "tests/boot/min_p.wk": b"11\n",       # elif 链（首条件真）
    "tests/boot/min_r.wk": b"11\n",       # elif 调用条件（首条件真）
    "tests/boot/min_t.wk": b"33\n",       # elif 调用条件（首条件假，else 命中）——elif 双吃鉴别用例
    "examples/hello.wk": "你好，Whisker！\n".encode("utf-8"),
}


def run(exe, timeout=30):
    p = subprocess.run([exe], capture_output=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


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
        shutil.copy(src, "build/lex_input.txt")
        try:
            code, out, err = run("build/wkcc2.exe")
        except subprocess.TimeoutExpired:
            failed.append((src, "编译超时"))
            continue
        if code != 0 or b"[wkcc]" in err or b"[wkcc]" in out:
            failed.append((src, "编译报错 exit=%d %s" % (code, (err or out)[:80])))
            continue
        try:
            code2, out2, _ = run("build/selfhost.exe")
        except subprocess.TimeoutExpired:
            failed.append((src, "运行超时"))
            continue
        if code2 != 0:
            failed.append((src, "运行崩溃 exit=%d" % code2))
        elif want is not None and out2 != want:
            failed.append((src, "输出 %r != 期望 %r" % (out2, want)))
        else:
            passed += 1
    for src, msg in failed:
        print("FAIL %s: %s" % (src, msg))
    print("==== 自举侧验收（wkcc2 语义）：{}/{} 通过 ====".format(passed, len(CASES)))
    return 0 if not failed else 1


if __name__ == "__main__":
    sys.exit(main())
