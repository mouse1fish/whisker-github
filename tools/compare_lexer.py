"""自举第 6 步验收：Whisker 版词法器 vs Python 版词法器，token 流逐行比对

用法（项目根目录）：  python tools/compare_lexer.py
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from whiskerc.cli import front_end                  # noqa: E402
from whiskerc.codegen_x64 import X64Program         # noqa: E402
from whiskerc.diag import Diag                      # noqa: E402
from whiskerc.lexer import tokenize                 # noqa: E402

TRICKY = """// 行注释
# 井号注释
/* 块注释
   跨行 */
actor Demo {
    a: Int = 1_000_000
    b: Int = 0xDE_AD_BE_EF
    hex2: Int = 0x2A
    s1: Str = "hello\\tworld\\n"
    s2: Str = '单引号 " 也可以'
    flag: Bool = True and not False

    on Run[x: Int] {
        arr: Int[8]
        arr[x % 8] = x / 3 - x * 2 + x % 5
        if x <= 10 and x >= 3 or x != 7 {
            print(intToStr(x), "..=", arr[x % 8])
        } elif x == 0 {
            print("?")
        } else {
            print("!==")
        }
        while x > 0 {
            x = x - 1
            if x == 5 { break }
        }
        for i in 0 ..= 2 {
            self.send(Tick(self))
        }
        q: Ptr = alloc(16)
        store64(q, load64(ptrAdd(q, 8)))
    }

    on Tick[who: ActorRef[Demo]] {
        who.send(Ping)
    }
}
"""


def main() -> int:
    # 1) 编译 Whisker 版词法器
    program, diag = front_end(ROOT / "tools" / "lexsource.wk")
    if not diag.ok():
        print(diag.render(str(ROOT / "tools" / "lexsource.wk")))
        return 1
    xp = X64Program(program)
    xp.emit()
    exe = ROOT / "build" / "lex.exe"
    exe.write_bytes(xp.pe.build(xp.a, xp.a.labels["whisker_entry"]))
    print("[whisker] 词法器编译完成：build/lex.exe")

    # 2) 准备样本：全部示例/测试 + 一个专给词法器的刁钻样本
    samples = sorted([*ROOT.glob("examples/**/*.wk"),
                      *ROOT.glob("tests/**/*.wk")])
    tricky = ROOT / "build" / "lex_tricky.wk"
    tricky.write_text(TRICKY, encoding="utf-8")
    samples.append(tricky)

    fails = 0
    total_tokens = 0
    for path in samples:
        text = path.read_text(encoding="utf-8-sig")
        d = Diag()
        toks = tokenize(text, d)
        py_lines = []
        for t in toks:
            body = "" if t.kind == "newline" else t.text
            py_lines.append(f"{t.kind}|{body}")

        shutil_src = ROOT / "build" / "lex_input.txt"
        shutil_src.write_text(text, encoding="utf-8")
        r = subprocess.run([str(exe)], capture_output=True, text=True, encoding="utf-8")
        wk_lines = [l for l in (r.stdout or "").split("\n") if l.strip() != ""]

        total_tokens += len(py_lines)
        # token 文本里可能含真实换行/制表符，所以按字节流比对（比按行更严格）
        expected = "".join(line + "\n" for line in py_lines)
        if r.stdout == expected:
            print(f"[PASS] {path.relative_to(ROOT)}（{len(py_lines)} 个 token）")
            continue
        fails += 1
        print(f"[FAIL] {path.relative_to(ROOT)}：python {len(py_lines)} vs whisker {len(wk_lines)} 行")
        shown = 0
        for i in range(max(len(py_lines), len(wk_lines))):
            a = py_lines[i] if i < len(py_lines) else "<缺>"
            b = wk_lines[i] if i < len(wk_lines) else "<缺>"
            if a != b:
                print(f"  第 {i} 个不同：python={a!r}  whisker={b!r}")
                shown += 1
                if shown >= 3:
                    break

    print("")
    if fails == 0:
        print(f"==== 词法器比对：{len(samples)} 份样本全部一致（共 {total_tokens} 个 token）====")
        return 0
    print(f"==== 词法器比对：{len(samples) - fails}/{len(samples)} 一致 ====")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())