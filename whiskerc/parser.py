"""Whisker 语法分析器

语句风格：Python 味（换行结束、条件不带括号、变量直接赋值即可出现）+ C 味（花括号分块、分号可选）
结构风格：花括号最大 / 中括号中等 / 圆括号最小
"""
from __future__ import annotations

from . import ast_nodes as A
from .diag import Diag
from .lexer import Token, TYPE_NAMES

# 二元运算符优先级（低 → 高）。`and`/`or` 与 `&&`/`||` 等价
BIN_LEVELS = [
    ["or", "||"],
    ["and", "&&"],
    ["==", "!="],
    ["<", "<=", ">", ">="],
    ["+", "-"],
    ["*", "/", "%"],
]


class ParseStop(Exception):
    pass


class Parser:
    def __init__(self, toks: list[Token], diag: Diag) -> None:
        self.toks = toks
        self.i = 0
        self.diag = diag

    # ---------- 基础工具 ----------
    def peek(self, k: int = 0) -> Token:
        idx = min(self.i + k, len(self.toks) - 1)
        return self.toks[idx]

    def at(self, kind: str, text: str | None = None) -> bool:
        t = self.peek()
        return t.kind == kind and (text is None or t.text == text)

    def next(self) -> Token:
        t = self.toks[self.i]
        if t.kind != "eof":
            self.i += 1
        return t

    def accept(self, kind: str, text: str | None = None) -> Token | None:
        if self.at(kind, text):
            return self.next()
        return None

    def skip_newlines(self) -> None:
        while self.at("newline"):
            self.next()

    def peek_after_newlines(self) -> Token:
        k = 0
        while self.peek(k).kind == "newline":
            k += 1
        return self.peek(k)

    def fail(self, msg: str, tok: Token | None = None) -> None:
        t = tok or self.peek()
        disp = t.text if t.kind != "eof" else "文件末尾"
        self.diag.error(t.line, t.col, f"{msg}（遇到 {disp}）")
        raise ParseStop()

    def expect(self, kind: str, text: str | None = None, what: str = "") -> Token:
        if self.at(kind, text):
            return self.next()
        want = what or (repr(text) if text is not None else kind)
        self.fail(f"期望 {want}")
        raise ParseStop()   # pragma: no cover

    def end_stmt(self) -> None:
        """语句结束：换行 / 分号 / 紧跟 } 或文件末尾（后两者可省略）"""
        saw = False
        while self.at("punc", ";") or self.at("newline"):
            self.next()
            saw = True
        if not saw and not (self.at("punc", "}") or self.at("eof")):
            self.fail("语句结束处需要换行（或分号）")

    # ---------- 顶层 ----------
    def parse(self) -> list[A.ActorDecl]:
        actors: list[A.ActorDecl] = []
        try:
            self.skip_newlines()
            while not self.at("eof"):
                if self.at("kw", "actor"):
                    actors.append(self.parse_actor())
                else:
                    self.fail("顶层只允许 actor 声明")
                self.skip_newlines()
        except ParseStop:
            pass
        return actors

    def parse_actor(self) -> A.ActorDecl:
        kw = self.expect("kw", "actor")
        name_tok = self.expect("ident", what="actor 名字")
        self.expect("punc", "{")
        self.skip_newlines()
        fields: list[A.FieldDecl] = []
        handlers: list[A.HandlerDecl] = []
        funcs: list[A.FuncDecl] = []
        while not self.at("punc", "}"):
            if self.at("eof"):
                self.fail("actor 主体没有闭合（缺少 }）")
            if self.at("kw", "on"):
                handlers.append(self.parse_handler())
            elif self.at("kw", "def"):
                funcs.append(self.parse_func())
            elif self.at("kw", "var") or self.at("kw", "let"):
                self.next()
                fields.append(self.parse_field())
            elif self.at("ident"):
                fields.append(self.parse_field())
            else:
                self.fail("actor 主体内只允许字段声明、def 函数或 on 消息处理")
            self.skip_newlines()
        self.expect("punc", "}")
        return A.ActorDecl(name_tok.text, fields, handlers, funcs, kw.line, kw.col)

    def parse_field(self) -> A.FieldDecl:
        name_tok = self.expect("ident", what="字段名")
        self.expect("punc", ":", "':'")
        type_expr = self.parse_type()
        init = None
        if self.accept("punc", "="):
            init = self.parse_expr()
        self.end_stmt()
        return A.FieldDecl(name_tok.text, type_expr, init, name_tok.line, name_tok.col)

    def parse_params_opt(self) -> list[A.Param]:
        """可选的 [ 参数列表 ]（中括号：中等层次）"""
        params: list[A.Param] = []
        if self.accept("punc", "["):
            self.skip_newlines()
            if not self.at("punc", "]"):
                while True:
                    p_tok = self.expect("ident", what="参数名")
                    self.expect("punc", ":", "':'")
                    p_type = self.parse_type()
                    params.append(A.Param(p_tok.text, p_type, p_tok.line, p_tok.col))
                    if not self.accept("punc", ","):
                        break
                    self.skip_newlines()
            self.skip_newlines()
            self.expect("punc", "]", "']'")
        return params

    def parse_handler(self) -> A.HandlerDecl:
        kw = self.expect("kw", "on")
        name_tok = self.expect("ident", what="消息名")
        params = self.parse_params_opt()
        body = self.parse_block()
        return A.HandlerDecl(name_tok.text, params, body, kw.line, kw.col)

    def parse_func(self) -> A.FuncDecl:
        kw = self.expect("kw", "def")
        name_tok = self.expect("ident", what="函数名")
        params = self.parse_params_opt()
        ret_expr = None
        if self.accept("punc", "->"):
            ret_expr = self.parse_type()
        body = self.parse_block()
        return A.FuncDecl(name_tok.text, params, ret_expr, body, kw.line, kw.col)

    def parse_type(self) -> A.TypeExpr:
        t = self.expect("ident", what="类型名")
        if t.text not in TYPE_NAMES:
            self.fail(f"未知类型 {t.text}（可用：Int / Bool / Str / ActorRef[某个 actor] / Int[长度]）", t)
        if t.text == "ActorRef":
            self.expect("punc", "[", "'['")
            inner = self.expect("ident", what="actor 名字")
            self.expect("punc", "]", "']'")
            return A.TypeExpr("ActorRef", inner.text, t.line, t.col)
        if self.at("punc", "["):               # 数组类型：Int[4096]
            self.next()
            size_tok = self.expect("int", what="数组长度（正整数）")
            self.expect("punc", "]", "']'")
            size = int(size_tok.text)
            if size <= 0:
                self.fail("数组长度必须是正整数", size_tok)
            return A.TypeExpr(t.text, None, t.line, t.col, size=size)
        return A.TypeExpr(t.text, None, t.line, t.col)

    # ---------- 语句 ----------
    def parse_block(self) -> list[A.Stmt]:
        self.expect("punc", "{")
        self.skip_newlines()
        stmts: list[A.Stmt] = []
        while not self.at("punc", "}"):
            if self.at("eof"):
                self.fail("语句块没有闭合（缺少 }）")
            stmts.append(self.parse_stmt())
            self.skip_newlines()
        self.expect("punc", "}")
        return stmts

    def parse_stmt(self) -> A.Stmt:
        t = self.peek()

        # 兼容旧写法：var / let 作为可忽略前缀
        if t.kind == "kw" and t.text in ("var", "let"):
            self.next()
            return self.parse_decl_or_assign()

        if t.kind == "kw" and t.text == "if":
            return self.parse_if()

        if t.kind == "kw" and t.text == "while":
            self.next()
            cond = self.parse_expr()            # 条件不需要括号，写了也能解析（当作括号表达式）
            body = self.parse_block()
            return A.WhileStmt(cond, body, t.line, t.col)

        if t.kind == "kw" and t.text == "for":
            self.next()
            name_tok = self.expect("ident", what="循环变量名")
            self.expect("kw", "in", "'in'")
            lo = self.parse_expr()
            if self.accept("punc", "..="):
                inclusive = True
            elif self.accept("punc", ".."):
                inclusive = False
            else:
                self.fail("区间循环要写 `a .. b`（不含上界）或 `a ..= b`（含上界）")
            hi = self.parse_expr()
            body = self.parse_block()
            return A.ForStmt(name_tok.text, lo, hi, inclusive, body, t.line, t.col)

        if t.kind == "kw" and t.text == "return":
            self.next()
            value = None
            if not (self.at("newline") or self.at("punc", ";") or self.at("punc", "}")
                    or self.at("eof")):
                value = self.parse_expr()
            self.end_stmt()
            return A.ReturnStmt(value, t.line, t.col)

        if t.kind == "kw" and t.text == "break":
            self.next()
            self.end_stmt()
            return A.BreakStmt(t.line, t.col)

        if t.kind == "kw" and t.text == "continue":
            self.next()
            self.end_stmt()
            return A.ContinueStmt(t.line, t.col)

        return self.parse_decl_or_assign()

    def parse_decl_or_assign(self) -> A.Stmt:
        t = self.peek()

        # 声明： name: 类型 = 值      （类型注解式，Python 味）
        if t.kind == "ident" and self.peek(1).kind == "punc" and self.peek(1).text == ":":
            self.next()
            self.next()                         # ':'
            type_expr = self.parse_type()
            init = None
            if self.accept("punc", "="):
                init = self.parse_expr()
            self.end_stmt()
            return A.VarStmt(t.text, type_expr, init, t.line, t.col)

        # 赋值或表达式语句
        expr = self.parse_expr()
        if self.at("punc", "="):
            eq = self.next()
            value = self.parse_expr()
            self.end_stmt()
            return A.AssignStmt(expr, value, eq.line, eq.col)
        self.end_stmt()
        return A.ExprStmt(expr, expr.line, expr.col)

    def parse_if(self) -> A.Stmt:
        t = self.expect("kw", "if")
        cond = self.parse_expr()
        then_body = self.parse_block()

        nxt = self.peek_after_newlines()
        if nxt.kind == "kw" and nxt.text in ("else", "elif"):
            self.skip_newlines()
            if self.at("kw", "elif"):
                kw = self.next()
                # elif → else { if ... }（语义等价，AST 复用 IfStmt）
                inner = self.parse_if_body(kw)
                return A.IfStmt(cond, then_body, [inner], t.line, t.col)
            self.expect("kw", "else")
            if self.at("kw", "if"):
                return A.IfStmt(cond, then_body, [self.parse_stmt()], t.line, t.col)
            else_body = self.parse_block()
            return A.IfStmt(cond, then_body, else_body, t.line, t.col)

        return A.IfStmt(cond, then_body, None, t.line, t.col)

    def parse_if_body(self, kw: Token) -> A.IfStmt:
        """解析 elif 之后的部分（条件 + 块 + 可能的后续 elif/else）"""
        cond = self.parse_expr()
        then_body = self.parse_block()
        nxt = self.peek_after_newlines()
        if nxt.kind == "kw" and nxt.text in ("else", "elif"):
            self.skip_newlines()
            if self.at("kw", "elif"):
                inner_kw = self.next()
                inner = self.parse_if_body(inner_kw)
                return A.IfStmt(cond, then_body, [inner], kw.line, kw.col)
            self.expect("kw", "else")
            if self.at("kw", "if"):
                return A.IfStmt(cond, then_body, [self.parse_stmt()], kw.line, kw.col)
            else_body = self.parse_block()
            return A.IfStmt(cond, then_body, else_body, kw.line, kw.col)
        return A.IfStmt(cond, then_body, None, kw.line, kw.col)

    # ---------- 表达式 ----------
    def parse_expr(self) -> A.Expr:
        return self.parse_bin(0)

    def parse_bin(self, level: int) -> A.Expr:
        if level >= len(BIN_LEVELS):
            return self.parse_unary()
        left = self.parse_bin(level + 1)
        while True:
            t = self.peek()
            if (t.kind == "punc" or t.kind == "kw") and t.text in BIN_LEVELS[level]:
                self.next()
                right = self.parse_bin(level + 1)
                left = A.Binary(t.text, left, right, t.line, t.col)
            else:
                return left

    def parse_unary(self) -> A.Expr:
        t = self.peek()
        if (t.kind == "punc" and t.text in ("-", "!")) or (t.kind == "kw" and t.text == "not"):
            self.next()
            operand = self.parse_unary()
            return A.Unary("!" if t.text == "not" else t.text, operand, t.line, t.col)
        return self.parse_postfix()

    def parse_postfix(self) -> A.Expr:
        e = self.parse_primary()
        while True:
            if self.at("punc", "["):            # 数组下标：buf[i]
                br = self.next()
                idx = self.parse_expr()
                self.expect("punc", "]")
                e = A.IndexExpr(e, idx, br.line, br.col)
                continue
            if self.at("punc", "."):
                dot = self.next()
                name_tok = self.expect("ident", what="成员名")
                if name_tok.text != "send":
                    self.fail(f"不支持成员访问 .{name_tok.text}（Actor 之间只能通过 ...send(消息) 通信）",
                              name_tok)
                self.expect("punc", "(", "'('")
                msg_tok = self.expect("ident", what="消息名")
                self.expect("punc", "(", "'('")
                args: list[A.Expr] = []
                if not self.at("punc", ")"):
                    while True:
                        args.append(self.parse_expr())
                        if not self.accept("punc", ","):
                            break
                self.expect("punc", ")")
                self.expect("punc", ")")
                e = A.SendExpr(e, msg_tok.text, args, dot.line, dot.col)
                continue
            return e

    def parse_primary(self) -> A.Expr:
        t = self.peek()

        if t.kind == "int":
            self.next()
            return A.IntLit(int(t.text), t.line, t.col)

        if t.kind == "str":
            self.next()
            return A.StrLit(t.text, t.line, t.col)

        if t.kind == "kw" and t.text in ("true", "false", "True", "False"):
            self.next()
            return A.BoolLit(t.text in ("true", "True"), t.line, t.col)

        if t.kind == "kw" and t.text == "self":
            self.next()
            return A.SelfExpr(t.line, t.col)

        if t.kind == "kw" and t.text == "spawn":
            self.next()
            name_tok = self.expect("ident", what="actor 名字")
            return A.SpawnExpr(name_tok.text, t.line, t.col)

        if t.kind == "ident":
            self.next()
            if self.at("punc", "("):
                self.next()
                args: list[A.Expr] = []
                if not self.at("punc", ")"):
                    while True:
                        args.append(self.parse_expr())
                        if not self.accept("punc", ","):
                            break
                self.expect("punc", ")")
                return A.Call(t.text, args, t.line, t.col)
            return A.Ident(t.text, t.line, t.col)

        if t.kind == "punc" and t.text == "(":
            self.next()
            e = self.parse_expr()
            self.expect("punc", ")")
            return e

        self.fail("这里需要一个表达式")
        raise ParseStop()   # pragma: no cover


def parse(toks: list[Token], diag: Diag) -> list[A.ActorDecl]:
    return Parser(toks, diag).parse()