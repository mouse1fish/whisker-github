"""AST 规范化转储：把 Python 前端解析出的 AST 按后序遍历打成一行一节点，
供自举第 8 步比对（Whisker 版解析器产出同样的行序列）。

用法：  python tools/astdump.py <file.wk>
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from whiskerc.cli import front_end      # noqa: E402
from whiskerc import ast_nodes as A     # noqa: E402


def esc(s: str) -> str:
    return s.replace("\\", "\\\\").replace("\n", "\\n").replace("\r", "\\r")


def te_str(te) -> str:
    """类型写法（语法层面的，不经过语义分析）"""
    if te is None:
        return "None"
    if te.name == "ActorRef":
        return f"ActorRef[{te.arg}]"
    if te.size is not None:
        return f"{te.name}[{te.size}]"
    return te.name


def walk_expr(e, out: list) -> None:
    if isinstance(e, A.IntLit):
        out.append(f"Int|{e.value}")
    elif isinstance(e, A.BoolLit):
        out.append(f"Bool|{1 if e.value else 0}")
    elif isinstance(e, A.StrLit):
        out.append(f"Str|{esc(e.value)}")
    elif isinstance(e, A.Ident):
        out.append(f"Ident|{esc(e.name)}")
    elif isinstance(e, A.SelfExpr):
        out.append("Self")
    elif isinstance(e, A.SpawnExpr):
        out.append(f"Spawn|{e.actor}")
    elif isinstance(e, A.Unary):
        walk_expr(e.operand, out)
        out.append(f"Unary|{e.op}")
    elif isinstance(e, A.Binary):
        walk_expr(e.left, out)
        walk_expr(e.right, out)
        out.append(f"Binary|{e.op}")
    elif isinstance(e, A.Call):
        for a in e.args:
            walk_expr(a, out)
        out.append(f"Call|{esc(e.name)}")
    elif isinstance(e, A.SendExpr):
        walk_expr(e.target, out)
        for a in e.args:
            walk_expr(a, out)
        out.append(f"Send|{esc(e.msg)}")
    elif isinstance(e, A.IndexExpr):
        walk_expr(e.obj, out)
        walk_expr(e.index, out)
        out.append("Index")
    else:
        raise AssertionError(type(e).__name__)


def walk_stmt(s, out: list) -> None:
    if isinstance(s, A.VarStmt):
        if s.init is not None:
            walk_expr(s.init, out)
        out.append(f"Var|{esc(s.name)}|{te_str(s.type_expr)}|{1 if s.init is not None else 0}")
    elif isinstance(s, A.AssignStmt):
        walk_stmt_or_expr_target(s.target, out)
        walk_expr(s.value, out)
        out.append("Assign")
    elif isinstance(s, A.ExprStmt):
        walk_expr(s.expr, out)
        out.append("ExprStmt")
    elif isinstance(s, A.IfStmt):
        walk_expr(s.cond, out)
        walk_block(s.then_body, out)
        if s.else_body:
            walk_block(s.else_body, out)
        out.append("If")
    elif isinstance(s, A.WhileStmt):
        walk_expr(s.cond, out)
        walk_block(s.body, out)
        out.append("While")
    elif isinstance(s, A.ForStmt):
        walk_expr(s.lo, out)
        walk_expr(s.hi, out)
        walk_block(s.body, out)
        out.append(f"For|{esc(s.name)}|{1 if s.inclusive else 0}")
    elif isinstance(s, A.ReturnStmt):
        if s.value is not None:
            walk_expr(s.value, out)
        out.append(f"Return|{1 if s.value is not None else 0}")
    elif isinstance(s, A.BreakStmt):
        out.append("Break")
    elif isinstance(s, A.ContinueStmt):
        out.append("Continue")
    else:
        raise AssertionError(type(s).__name__)


def walk_stmt_or_expr_target(t, out: list) -> None:
    if isinstance(t, A.IndexExpr):
        walk_expr(t.obj, out)
        walk_expr(t.index, out)
        out.append("Index")
    else:
        walk_expr(t, out)


def walk_block(body, out: list) -> None:
    for s in body:
        walk_stmt(s, out)


def walk_member(m, out: list) -> None:
    if isinstance(m, A.FieldDecl):
        if m.init is not None:
            walk_expr(m.init, out)
        out.append(f"Field|{esc(m.name)}|{te_str(m.type_expr)}|{1 if m.init is not None else 0}")
    elif isinstance(m, A.HandlerDecl):
        for p in m.params:
            out.append(f"Param|{esc(p.name)}|{te_str(p.type_expr)}")
        walk_block(m.body, out)
        out.append(f"Handler|{esc(m.name)}|{len(m.params)}")
    elif isinstance(m, A.FuncDecl):
        for p in m.params:
            out.append(f"Param|{esc(p.name)}|{te_str(p.type_expr)}")
        walk_block(m.body, out)
        out.append(f"Func|{esc(m.name)}|{te_str(m.ret_expr)}|{len(m.params)}")
    else:
        raise AssertionError(type(m).__name__)


def dump_program(program) -> str:
    out: list[str] = []
    for a in program.actors:
        members = [*a.fields, *a.handlers, *a.funcs]
        members.sort(key=lambda m: m.line)      # 按源码顺序（字段/处理/函数分开存，行号还原顺序）
        for m in members:
            walk_member(m, out)
        out.append(f"Actor|{esc(a.name)}")
    out.append(f"Program|{len(program.actors)}")
    return "".join(line + "\n" for line in out)


def main() -> int:
    path = Path(sys.argv[1])
    program, diag = front_end(path)
    if not diag.ok():
        print(diag.render(str(path)), file=sys.stderr)
        return 1
    sys.stdout.write(dump_program(program))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())