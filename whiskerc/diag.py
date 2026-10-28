"""Whisker 编译器 —— 诊断信息收集"""
from __future__ import annotations

MAX_ERRORS = 30


class Diag:
    def __init__(self) -> None:
        self.items: list[tuple[str, int, int, str]] = []   # (kind, line, col, msg)

    def error(self, line: int, col: int, msg: str) -> None:
        self.items.append(("error", line, col, msg))

    def warn(self, line: int, col: int, msg: str) -> None:
        self.items.append(("warning", line, col, msg))

    @property
    def errors(self) -> list[tuple[str, int, int, str]]:
        return [i for i in self.items if i[0] == "error"]

    @property
    def warnings(self) -> list[tuple[str, int, int, str]]:
        return [i for i in self.items if i[0] == "warning"]

    def ok(self) -> bool:
        return not self.errors

    def too_many(self) -> bool:
        return len(self.errors) >= MAX_ERRORS

    def render(self, path: str) -> str:
        if not self.items:
            return ""
        src = None
        try:
            with open(path, "r", encoding="utf-8") as f:
                src = f.read().splitlines()
        except OSError:
            pass
        out = []
        for kind, line, col, msg in sorted(self.items, key=lambda i: (i[1], i[2])):
            tag = "错误" if kind == "error" else "警告"
            out.append(f"{path}:{line}:{col}: {tag}: {msg}")
            if src and 1 <= line <= len(src):
                text = src[line - 1]
                out.append("    " + text)
                out.append("    " + " " * max(0, col - 1) + "^")
        n_err = len(self.errors)
        n_warn = len(self.warnings)
        out.append(f"—— {n_err} 个错误，{n_warn} 个警告 ——")
        return "\n".join(out)