"""Whisker 词法分析器

语句风格（Python 味 + C 味）：
  - 换行即语句结束（无需分号）；分号仍可写，C 背景的人顺手
  - 圆括号/中括号/花括号内部的换行自动忽略（Python 的隐式行连接）
  - `#` 和 `//` 都是行注释
  - 单引号、双引号都能写字符串；数字可用下划线分隔（1_000_000）
  - `and`/`or`/`not` 与 `&&`/`||`/`!` 等价；`True`/`False` 与 `true`/`false` 等价
"""
from __future__ import annotations

from .diag import Diag

KEYWORDS = {
    "actor", "on", "if", "else", "elif", "while", "for", "in", "spawn", "self",
    "return", "break", "continue", "def",
    "and", "or", "not",
    "true", "false", "True", "False",
    "var", "let",            # 兼容旧写法：作为可忽略的前缀保留
}

PUNCS = [
    "..=", "..", "->", "&&", "||", "==", "!=", "<=", ">=",
    "(", ")", "{", "}", "[", "]", ",", ":", ";",
    "=", "<", ">", "+", "-", "*", "/", "%", "!", ".", "?",
]

TYPE_NAMES = {"Int", "Bool", "Str", "ActorRef", "Ptr"}

# 只有圆括号/中括号内部的换行被忽略（隐式续行）；
# 花括号是「装语句的块」，里面的换行必须保留 —— 否则换行没法当语句结束符。
OPENERS = {"(", "["}
CLOSERS = {")", "]"}


class Token:
    __slots__ = ("kind", "text", "line", "col")

    def __init__(self, kind: str, text: str, line: int, col: int) -> None:
        self.kind = kind      # int | str | ident | kw | punc | newline | eof
        self.text = text
        self.line = line
        self.col = col

    def __repr__(self) -> str:      # pragma: no cover
        return f"Token({self.kind},{self.text!r},{self.line}:{self.col})"


ESCAPES = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "'": "'", "\\": "\\", "0": "\0"}


def tokenize(src: str, diag: Diag) -> list[Token]:
    toks: list[Token] = []
    i = 0
    line = 1
    col = 1
    n = len(src)
    depth = 0                      # 括号嵌套深度：>0 时换行被忽略

    def advance(k: int = 1) -> None:
        nonlocal i, col
        i += k
        col += k

    def push(kind: str, text: str, ln: int, cl: int) -> None:
        toks.append(Token(kind, text, ln, cl))

    def push_newline(ln: int, cl: int) -> None:
        if depth == 0 and toks and toks[-1].kind != "newline":
            push("newline", "\n", ln, cl)

    while i < n:
        c = src[i]

        if c == "\n":
            push_newline(line, col)
            i += 1
            line += 1
            col = 1
            continue

        if c in " \t\r":
            advance()
            continue

        # 行注释：# 或 //
        if c == "#" or (c == "/" and i + 1 < n and src[i + 1] == "/"):
            while i < n and src[i] != "\n":
                advance()
            continue

        # 块注释
        if c == "/" and i + 1 < n and src[i + 1] == "*":
            start_line, start_col = line, col
            advance(2)
            closed = False
            while i < n:
                if src[i] == "*" and i + 1 < n and src[i + 1] == "/":
                    advance(2)
                    closed = True
                    break
                if src[i] == "\n":
                    i += 1
                    line += 1
                    col = 1
                else:
                    advance()
            if not closed:
                diag.error(start_line, start_col, "块注释没有闭合（缺少 */）")
            continue

        # 字符串：单引号/双引号都行
        if c in ('"', "'"):
            quote = c
            start_line, start_col = line, col
            advance()
            buf: list[str] = []
            closed = False
            while i < n:
                ch = src[i]
                if ch == quote:
                    advance()
                    closed = True
                    break
                if ch == "\n":
                    break
                if ch == "\\":
                    if i + 1 >= n:
                        break
                    esc = src[i + 1]
                    if esc in ESCAPES:
                        buf.append(ESCAPES[esc])
                        advance(2)
                        continue
                    diag.error(line, col, f"不认识的转义字符 \\{esc}")
                    advance(2)
                    continue
                buf.append(ch)
                advance()
            if not closed:
                diag.error(start_line, start_col, "字符串没有闭合（缺少引号）")
            push("str", "".join(buf), start_line, start_col)
            continue

        # 整数：十进制（支持 1_000_000 下划线）或十六进制 0x2A
        if c.isdigit():
            start_line, start_col = line, col
            if c == "0" and i + 1 < n and src[i + 1] in "xX":
                advance(2)
                j = i
                while j < n and (src[j].isdigit() or src[j].lower() in "abcdef" or src[j] == "_"):
                    j += 1
                digits = src[i:j].replace("_", "")
                if not digits:
                    diag.error(start_line, start_col, "0x 后面缺少十六进制数字")
                advance(j - i)
                push("int", str(int(digits or "0", 16)), start_line, start_col)
                continue
            j = i
            while j < n and (src[j].isdigit() or src[j] == "_"):
                j += 1
            text = src[i:j].replace("_", "")
            advance(j - i)
            push("int", text, start_line, start_col)
            continue

        # 标识符 / 关键字
        if c.isalpha() or c == "_":
            start_line, start_col = line, col
            j = i
            while j < n and (src[j].isalnum() or src[j] == "_"):
                j += 1
            text = src[i:j]
            advance(j - i)
            push("kw" if text in KEYWORDS else "ident", text, start_line, start_col)
            continue

        # 运算符 / 分隔符
        for p in PUNCS:
            if src.startswith(p, i):
                if p in OPENERS:
                    depth += 1
                elif p in CLOSERS and depth > 0:
                    depth -= 1
                push("punc", p, line, col)
                advance(len(p))
                break
        else:
            diag.error(line, col, f"无法识别的字符 {c!r}")
            advance()

        if diag.too_many():
            break

    push_newline(line, col)
    toks.append(Token("eof", "<eof>", line, col))
    return toks