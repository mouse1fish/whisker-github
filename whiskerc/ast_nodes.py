"""Whisker 抽象语法树"""
from __future__ import annotations

from typing import Optional

from .typesys import Ty


class Node:
    __slots__ = ("line", "col")


# ---------------- 类型 ----------------
class TypeExpr(Node):
    __slots__ = ("name", "arg", "size")

    def __init__(self, name: str, arg: Optional[str], line: int, col: int,
                 size: Optional[int] = None) -> None:
        self.name = name
        self.arg = arg
        self.size = size        # 数组长度：Int[4096]
        self.line = line
        self.col = col


# ---------------- 声明 ----------------
class Param(Node):
    __slots__ = ("name", "type_expr", "ty")

    def __init__(self, name: str, type_expr: TypeExpr, line: int, col: int) -> None:
        self.name = name
        self.type_expr = type_expr
        self.ty: Ty = None  # type: ignore[assignment]
        self.line = line
        self.col = col


class FieldDecl(Node):
    __slots__ = ("name", "type_expr", "init", "ty")

    def __init__(self, name: str, type_expr: Optional[TypeExpr], init: Optional["Expr"], line: int, col: int) -> None:
        self.name = name
        self.type_expr = type_expr
        self.init = init
        self.ty: Ty = None  # type: ignore[assignment]
        self.line = line
        self.col = col


class HandlerDecl(Node):
    __slots__ = ("name", "params", "body", "actor")

    def __init__(self, name: str, params: list[Param], body: list["Stmt"], line: int, col: int) -> None:
        self.name = name
        self.params = params
        self.body = body
        self.actor: str = ""
        self.line = line
        self.col = col


class FuncDecl(Node):
    """actor 内的函数（用 def 声明，可以访问本 actor 的字段，可以递归）"""
    __slots__ = ("name", "params", "ret_expr", "ret_ty", "body", "actor")

    def __init__(self, name: str, params: list[Param], ret_expr: Optional[TypeExpr],
                 body: list["Stmt"], line: int, col: int) -> None:
        self.name = name
        self.params = params
        self.ret_expr = ret_expr
        self.ret_ty: Ty = None      # type: ignore[assignment]
        self.body = body
        self.actor: str = ""
        self.line = line
        self.col = col


class ActorDecl(Node):
    __slots__ = ("name", "fields", "handlers", "funcs")

    def __init__(self, name: str, fields: list[FieldDecl], handlers: list[HandlerDecl],
                 funcs: list[FuncDecl], line: int, col: int) -> None:
        self.name = name
        self.fields = fields
        self.handlers = handlers
        self.funcs = funcs
        self.line = line
        self.col = col


class Program:
    __slots__ = ("actors", "path")

    def __init__(self, actors: list[ActorDecl], path: str) -> None:
        self.actors = actors
        self.path = path


# ---------------- 语句 ----------------
class Stmt(Node):
    __slots__ = ()


class VarStmt(Stmt):
    __slots__ = ("name", "type_expr", "init", "ty")

    def __init__(self, name: str, type_expr: Optional[TypeExpr], init: "Expr", line: int, col: int) -> None:
        self.name = name
        self.type_expr = type_expr
        self.init = init
        self.ty: Ty = None  # type: ignore[assignment]
        self.line = line
        self.col = col


class AssignStmt(Stmt):
    __slots__ = ("target", "value")

    def __init__(self, target: "Expr", value: "Expr", line: int, col: int) -> None:
        self.target = target
        self.value = value
        self.line = line
        self.col = col


class ExprStmt(Stmt):
    __slots__ = ("expr",)

    def __init__(self, expr: "Expr", line: int, col: int) -> None:
        self.expr = expr
        self.line = line
        self.col = col


class IfStmt(Stmt):
    __slots__ = ("cond", "then_body", "else_body")

    def __init__(self, cond: "Expr", then_body: list[Stmt], else_body: Optional[list[Stmt]], line: int, col: int) -> None:
        self.cond = cond
        self.then_body = then_body
        self.else_body = else_body
        self.line = line
        self.col = col


class WhileStmt(Stmt):
    __slots__ = ("cond", "body")

    def __init__(self, cond: "Expr", body: list[Stmt], line: int, col: int) -> None:
        self.cond = cond
        self.body = body
        self.line = line
        self.col = col


class ForStmt(Stmt):
    """for i in a .. b { }   区间循环：`..` 不含上界，`..=` 含上界"""
    __slots__ = ("name", "lo", "hi", "inclusive", "body", "slot")

    def __init__(self, name: str, lo: "Expr", hi: "Expr", inclusive: bool,
                 body: list[Stmt], line: int, col: int) -> None:
        self.name = name
        self.lo = lo
        self.hi = hi
        self.inclusive = inclusive
        self.body = body
        self.line = line
        self.col = col


class ReturnStmt(Stmt):
    __slots__ = ("value", "ty", "func")

    def __init__(self, value: Optional["Expr"], line: int, col: int) -> None:
        self.value = value
        self.ty: Ty = None      # type: ignore[assignment]
        self.func: FuncDecl | None = None
        self.line = line
        self.col = col


class BreakStmt(Stmt):
    __slots__ = ()

    def __init__(self, line: int, col: int) -> None:
        self.line = line
        self.col = col


class ContinueStmt(Stmt):
    __slots__ = ()

    def __init__(self, line: int, col: int) -> None:
        self.line = line
        self.col = col


# ---------------- 表达式 ----------------
class Expr(Node):
    __slots__ = ("ty",)

    def __init__(self, line: int, col: int) -> None:
        self.ty: Ty = None  # type: ignore[assignment]
        self.line = line
        self.col = col


class IntLit(Expr):
    __slots__ = ("value",)

    def __init__(self, value: int, line: int, col: int) -> None:
        super().__init__(line, col)
        self.value = value


class BoolLit(Expr):
    __slots__ = ("value",)

    def __init__(self, value: bool, line: int, col: int) -> None:
        super().__init__(line, col)
        self.value = value


class StrLit(Expr):
    __slots__ = ("value",)

    def __init__(self, value: str, line: int, col: int) -> None:
        super().__init__(line, col)
        self.value = value


class Ident(Expr):
    __slots__ = ("name", "ref", "actor")

    def __init__(self, name: str, line: int, col: int) -> None:
        super().__init__(line, col)
        self.name = name
        self.ref: tuple[str, str] | None = None   # ('param'|'local'|'field', name)
        self.actor: str = ""


class SelfExpr(Expr):
    __slots__ = ("actor",)

    def __init__(self, line: int, col: int) -> None:
        super().__init__(line, col)
        self.actor = ""


class SpawnExpr(Expr):
    __slots__ = ("actor",)

    def __init__(self, actor: str, line: int, col: int) -> None:
        super().__init__(line, col)
        self.actor = actor


class Unary(Expr):
    __slots__ = ("op", "operand")

    def __init__(self, op: str, operand: Expr, line: int, col: int) -> None:
        super().__init__(line, col)
        self.op = op
        self.operand = operand


class Binary(Expr):
    __slots__ = ("op", "left", "right")

    def __init__(self, op: str, left: Expr, right: Expr, line: int, col: int) -> None:
        super().__init__(line, col)
        self.op = op
        self.left = left
        self.right = right


class Call(Expr):
    """函数调用：print/nowMs 之类的内置，或本 actor 里 def 声明的函数"""
    __slots__ = ("name", "args", "target")

    def __init__(self, name: str, args: list[Expr], line: int, col: int) -> None:
        super().__init__(line, col)
        self.name = name
        self.args = args
        self.target: FuncDecl | None = None     # 解析到用户函数时填上


class SendExpr(Expr):
    """target.send(Msg(args))"""
    __slots__ = ("target", "msg", "args", "target_actor", "handler")

    def __init__(self, target: Expr, msg: str, args: list[Expr], line: int, col: int) -> None:
        super().__init__(line, col)
        self.target = target
        self.msg = msg
        self.args = args
        self.target_actor: str = ""
        self.handler: HandlerDecl | None = None


class IndexExpr(Expr):
    """数组下标：buf[i]（读或写）"""
    __slots__ = ("obj", "index", "elem_ty", "arr_ty")

    def __init__(self, obj: Expr, index: Expr, line: int, col: int) -> None:
        super().__init__(line, col)
        self.obj = obj
        self.index = index
        self.elem_ty = None     # type: ignore[assignment]
        self.arr_ty = None      # type: ignore[assignment]