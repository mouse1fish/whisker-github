"""自举比对：Whisker 版词法器 vs Python 版词法器（token 流逐字节比对）

用法（项目根目录）：  python tools/compare_parser.py
说明：验证 Whisker 写的词法器与 Python 前端的词法器产出完全相同的 token 流。
     AST 比对需要 dump 版解析器（tools/astdump_compiler.wk，待重建）。
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
from whiskerc.lexer import tokenize                 # noqa: E402
from whiskerc.diag import Diag                      # noqa: E402


def main() -> int:
    # 1) 编译 Whisker 版词法器（用 lexsource.wk）
    program, diag = front_end(ROOT / "tools" / "lexsource.wk")
    if not diag.ok():
        print(diag.render(str(ROOT / "tools" / "lexsource.wk")))
        return 1
    xp = X64Program(program)
    xp.emit()
    exe = ROOT / "build" / "wkcc.exe"
    exe.write_bytes(xp.pe.build(xp.a, xp.a.labels["whisker_entry"]))
    print("[whisker] 词法器编译完成：build/wkcc.exe")

    # 2) 样本
    samples = sorted([*ROOT.glob("examples/**/*.wk"),
                      *ROOT.glob("tests/**/*.wk")])

    fails = 0
    total_tokens = 0
    for path in samples:
        text = path.read_text(encoding="utf-8-sig")

        # Python 前端词法
        d = Diag()
        toks = tokenize(text, d)
        py_lines = []
        for t in toks:
            body = "" if t.kind == "newline" else t.text
            py_lines.append(f"{t.kind}|{body}")

        # Whisker 前端词法
        inbox = ROOT / "build" / "lex_input.txt"
        inbox.write_text(text, encoding="utf-8")
        r = subprocess.run([str(exe)], capture_output=True, text=True, encoding="utf-8")
        wk_lines = [l for l in (r.stdout or "").split("\n") if l.strip() != ""]

        total_tokens += len(py_lines)
        expected = "".join(line + "\n" for line in py_lines)
        if r.stdout == expected:
            print(f"[PASS] {path.relative_to(ROOT)}（{len(py_lines)} 个 token）")
            continue
        fails += 1
        print(f"[FAIL] {path.relative_to(ROOT)}：python {len(py_lines)} vs whisker {len(wk_lines)}")
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
        print(f"==== 词法比对：{len(samples)} 份样本全部一致（共 {total_tokens} 个 token）====")
        return 0
    print(f"==== 词法比对：{len(samples) - fails}/{len(samples)} 一致 ====")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())