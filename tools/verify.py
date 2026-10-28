"""Whisker 验收脚本

用自研 x64 后端编译并运行全部正例，核对输出；再确认反例会在编译期被拦下。

用法（项目根目录）：  python tools/verify.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from whiskerc.cli import front_end          # noqa: E402
from whiskerc.codegen_x64 import X64Program  # noqa: E402

# (源文件, 输出中必须出现的片段)
GOOD: list[tuple[str, list[str]]] = [
    ("examples/hello.wk", ["你好，Whisker！"]),
    ("examples/counter.wk", ["Counter 累加结果 = 42"]),
    ("examples/pingpong.wk", ["链条结束，最后一跳编号 = 200001",
                                   "两方累计跳数 = 200001（期望 200001）"]),
    ("examples/fanout.wk", ["结果校验：与串行完全一致", "66566700000000"]),
    ("examples/syntax.wk", ["hits = 200646（期望 200646）",
                                 "sum = 2597497259（期望 2597497259）",
                                 "hello, whisker"]),
    ("tests/ordering.wk", ["收到 100000 条 | 序号错乱 0 条"]),
    ("tests/sieve.wk", ["小于 30000 的素数个数 = 3245"]),
    ("tests/mapreduce.wk", ["32 个分片汇总结果 = 6175887203"]),
    ("tests/bank.wk", ["三账户总额 = 6000（期望 6000）"]),
    ("tests/x64/selfsend.wk", ["累加完成 n = 5151"]),
    ("tests/x64/spawn.wk", ["收到 Pong(3) 累计 6"]),
    ("tests/x64/conditions.wk", ["a=16 b=12 c=57 e=16",
                                      "单独判断 and：true  false",
                                      "单独判断 or： true  false",
                                      "单独判断 not：true  false"]),
    ("tests/x64/branches.wk", ["A  h = 200646", "B  s = 3333383330"]),
    ("tests/x64/funcs.wk", ["square(9) = 81（期望 81）",
                                 "sum_to(100) = 5050（期望 5050）",
                                 "fib(20) = 6765（期望 6765）",
                                 "first_multiple_over[7, 100] = 105（期望 105）",
                                 "count_odds_to(100) = 50（期望 50）",
                                 "base + square(3) = 16（期望 16）",
                                 "n 的一半 = 50"]),
    ("tests/x64/divmod.wk", ["sum(i % 1000) = 49950000（期望 49950000）",
                                  "sum(i / 7) = 714250000（期望 714250000）",
                                  "-17 / 5 = -3 -17 % 5 = -2（期望 -3 -2）",
                                  "17 / -5 = -3 17 % -5 = 2（期望 -3 2）",
                                  "12345 / 1 = 12345 12345 % 1 = 0（期望 12345 0）"]),
    ("tests/x64/arrays.wk", ["局部数组平方和 = 1240（期望 1240）",
                                  "字段数组初始求和 = 0（期望 0）",
                                  "fill_slot 之后求和 = 828（期望 828）",
                                  "写入字节数 = 128（期望 128）",
                                  "读回字节数 = 128（期望 128）",
                                  "逐元素一致 = true（期望 True）"]),
    ("examples/wko.wk", ["wko 写入字节数 = 160（期望 160）",
                              "wko 读回字节数 = 160（期望 160）",
                              "magic/版本/长度 = true true true（期望 true true true）",
                              "载荷校验 = true（期望 true）"]),
    ("tests/x64/ptr.wk", ["缓冲区长度 = 300（期望 300）",
                               "容量 = 512（期望 512）",
                               "内容一致 = true（期望 True）",
                               "拼接结果 = 第 42 号（期望 第 42 号）",
                               "拼接长度(字节) = 10（期望 10）",
                               "写文件字节数 = 300（期望 300）"]),
]

BAD: list[tuple[str, str]] = [
    ("examples/bad/wrong_message.wk", "没有消息 on Decrement"),
    ("examples/bad/type_mismatch.wk", "应为 Int，实际是 Str"),
    ("examples/bad/type_mismatch.wk", "if 的条件必须是 Bool"),
]


def run_exe(exe: Path) -> tuple[int, str]:
    r = subprocess.run([str(exe)], capture_output=True, text=True, encoding="utf-8")
    return r.returncode, (r.stdout or "") + (r.stderr or "")


def build_x64(program, name: str) -> Path:
    xp = X64Program(program)
    xp.emit()
    data = xp.pe.build(xp.a, xp.a.labels["whisker_entry"])
    out = ROOT / "build" / f"{name}.exe"
    out.write_bytes(data)
    return out


def main() -> int:
    results: list[bool] = []

    for src, expect in GOOD:
        path = ROOT / src
        program, diag = front_end(path)
        if not diag.ok():
            print(f"[FAIL] {src} 前端报错\n{diag.render(str(path))}")
            results.append(False)
            continue
        exe = build_x64(program, path.stem)
        rc, text = run_exe(exe)
        ok = rc == 0 and all(e in text for e in expect)
        print(f"[{'PASS' if ok else 'FAIL'}] {src}（退出码 {rc}）")
        if not ok:
            print("---- 实际输出 ----\n" + text)
        results.append(ok)

    for src, expect_msg in BAD:
        path = ROOT / src
        _p, diag = front_end(path)
        msgs = "\n".join(m for _k, _l, _c, m in diag.items)
        ok = (not diag.ok()) and (expect_msg in msgs)
        print(f"[{'PASS' if ok else 'FAIL'}] {src} 编译期被拦下：{expect_msg}")
        results.append(ok)

    print("")
    print(f"==== 验收结果：{sum(results)}/{len(results)} 通过 ====")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())