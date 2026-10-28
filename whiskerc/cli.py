"""Whisker 编译器命令行接口

用法（在项目根目录）：
    python -m whiskerc check examples/counter.whisker     只做前端检查
    python -m whiskerc build examples/counter.whisker     编译成 build/<名字>.exe
    python -m whiskerc run   examples/counter.whisker     编译并运行

后端：自研 x86-64 后端（默认也是唯一）——直接产出 PE exe，不用 C / C++ / LLVM / 链接器。

可选参数： -o 名字 / --dump-asm
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from .ast_nodes import Program
from .codegen_x64 import X64Program
from .diag import Diag
from .lexer import tokenize
from .parser import parse
from .sema import Sema

ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "build"


def front_end(path: Path) -> tuple[Program, Diag]:
    try:
        src = path.read_text(encoding="utf-8-sig")      # 容忍编辑器写入的 BOM
    except OSError as exc:
        diag = Diag()
        diag.error(1, 1, f"无法读取源文件：{exc}")
        return Program([], str(path)), diag

    diag = Diag()
    toks = tokenize(src, diag)
    actors = parse(toks, diag)
    program = Program(actors, path.name)
    if diag.ok():
        Sema(actors, diag).run()
    return program, diag


def report(path: Path, diag: Diag) -> None:
    if diag.items:
        print(diag.render(str(path)), file=sys.stderr)


def build_x64(program: Program, name: str, dump_asm: bool = False) -> Path:
    xp = X64Program(program)
    xp.emit()
    if dump_asm:
        print(f"[whisker] 机器码清单（{len(xp.a.code)} 字节）")
        for off, note in xp.a.listing:
            print(f"  {off:06X}  {note}")
    entry = xp.a.labels["whisker_entry"]
    data = xp.pe.build(xp.a, entry)
    BUILD_DIR.mkdir(exist_ok=True)
    exe = BUILD_DIR / f"{name}.exe"
    exe.write_bytes(data)
    return exe


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="whiskerc", description="Whisker 编译器")
    sub = ap.add_subparsers(dest="cmd", required=True)
    for name, help_text in (("check", "只做词法/语法/语义检查"),
                            ("build", "编译成 build/<名字>.exe"),
                            ("run", "编译后立即运行")):
        p = sub.add_parser(name, help=help_text)
        p.add_argument("file", help=".whisker 源文件")
        p.add_argument("-o", "--out", default=None, help="产物名字（默认取文件名）")
        p.add_argument("--dump-asm", action="store_true", help="打印机器码清单")

    args = ap.parse_args(argv)
    path = Path(args.file)
    program, diag = front_end(path)
    report(path, diag)
    if not diag.ok():
        print(f"[whisker] {len(diag.errors)} 个错误，未生成任何代码", file=sys.stderr)
        return 1

    if args.cmd == "check":
        print(f"[whisker] {path.name} 检查通过（{len(program.actors)} 个 actor）")
        return 0

    name = args.out or path.stem
    exe = build_x64(program, name, dump_asm=args.dump_asm)
    print(f"[whisker] 成功（自研 x64 后端，无 C/LLVM/链接器参与）：{exe}")

    if args.cmd == "run":
        print(f"[whisker] 运行 {exe.name} …")
        rc = subprocess.call([str(exe)])
        print(f"[whisker] 进程退出码 {rc}")
    return 0


if __name__ == "__main__":      # pragma: no cover
    raise SystemExit(main())