"""Whisker 代码生成后端（M0：C 引导后端）

映射约定（每个 actor 一套私有命名前缀，避免与 C 关键字/标准库撞名）：

    A_<actor>       Actor 结构体
    E_<actor>       消息信封（tag + 载荷 union）
    M_<actor>_<msg> 单条消息的载荷结构体
    T_<actor>_<msg> 消息 tag 枚举
    D_<actor>       消息分发函数
    H_<actor>_<msg> 消息处理函数
    N_<actor>       构造（spawn）
    I_<actor>       初始化字段

    源语言里的字段/参数/局部变量统一加前缀 v_，避免撞上 C 关键字（例如源码里叫 int 也不会出事）。

    "无共享可变状态"在这里是结构性成立的：每个 Actor 的结构体只被自己的
    处理函数访问，而处理函数永远在且仅在一个工作线程上跑；跨 Actor 的数据
    只能通过消息信封（值拷贝）传递。
"""
from __future__ import annotations

from . import ast_nodes as A

IND = "    "


def c_string(s: str) -> str:
    out = []
    for ch in s:
        if ch == "\\":
            out.append("\\\\")
        elif ch == '"':
            out.append('\\"')
        elif ch == "\n":
            out.append("\\n")
        elif ch == "\r":
            out.append("\\r")
        elif ch == "\t":
            out.append("\\t")
        else:
            out.append(ch)
    return '"' + "".join(out) + '"'


class CEmitter:
    def __init__(self, program: A.Program, entry_actor: str = "Main", entry_msg: str = "Start",
                 workers: int = 0) -> None:
        self.program = program
        self.entry_actor = entry_actor
        self.entry_msg = entry_msg
        self.workers = workers
        self.tmp = 0
        self.locals: set[str] = set()   # 当前处理函数里已经声明过的 C 局部名

    # ---------------- 顶层 ----------------
    def emit(self) -> str:
        L: list[str] = []
        L.append(f"/* 由 whiskerc 生成的 C 代码（源文件：{self.program.path}） */")
        L.append("/* 这是 M0 的「C 引导后端」，仅用于自举验证；正式后端是自研 LLVM IR 后端。 */")
        L.append("")
        L.append('#include "whisker_runtime.h"')
        L.append("#include <stdint.h>")
        L.append("#include <stdbool.h>")
        L.append("")

        for a in self.program.actors:
            L += self.actor_struct(a)
        for a in self.program.actors:
            L += self.actor_messages(a)
        for a in self.program.actors:
            L += self.forward_decls(a)
        for a in self.program.actors:
            L += self.handler_defs(a)
        for a in self.program.actors:
            L += self.dispatch_def(a)
        for a in self.program.actors:
            L += self.new_def(a)
        L += self.main_def()
        return "\n".join(L) + "\n"

    # ---------------- 结构体 ----------------
    def actor_struct(self, a: A.ActorDecl) -> list[str]:
        L = [f"typedef struct A_{a.name} {{", f"{IND}WhiskerActor base;"]
        for f in a.fields:
            L.append(f"{IND}{f.ty.c_type()} v_{f.name};")
        L.append(f"}} A_{a.name};")
        L.append("")
        return L

    def actor_messages(self, a: A.ActorDecl) -> list[str]:
        L: list[str] = []
        if a.handlers:
            for h in a.handlers:
                if h.params:
                    fields = " ".join(f"{p.ty.c_type()} v_{p.name};" for p in h.params)
                else:
                    fields = "int32_t _unused;"
                L.append(f"typedef struct M_{a.name}_{h.name} {{ {fields} }} M_{a.name}_{h.name};")
            tags = ", ".join(f"T_{a.name}_{h.name} = {i + 1}" for i, h in enumerate(a.handlers))
            L.append(f"enum {{ {tags} }};")
            members = " ".join(f"M_{a.name}_{h.name} h_{h.name};" for h in a.handlers)
        else:
            members = "int32_t _unused;"
        L.append(f"typedef struct E_{a.name} {{ int32_t tag; union {{ {members} }} u; }} E_{a.name};")
        L.append("")
        return L

    def forward_decls(self, a: A.ActorDecl) -> list[str]:
        L = [f"static void D_{a.name}(WhiskerActor* a, void* payload);",
             f"static A_{a.name}* N_{a.name}(void);"]
        for h in a.handlers:
            params = "".join(f", {p.ty.c_type()} v_{p.name}" for p in h.params)
            L.append(f"static void H_{a.name}_{h.name}(A_{a.name}* self{params});")
        L.append("")
        return L

    # ---------------- 处理函数 ----------------
    def handler_defs(self, a: A.ActorDecl) -> list[str]:
        L: list[str] = []
        for h in a.handlers:
            params = "".join(f", {p.ty.c_type()} v_{p.name}" for p in h.params)
            self.locals = {p.name for p in h.params}      # 形参在 C 里已经声明过了
            L.append(f"static void H_{a.name}_{h.name}(A_{a.name}* self{params}) {{")
            body = self.stmts(h.body, IND)
            L += body if body else [f"{IND}(void)self;"]
            L.append("}")
            L.append("")
        return L

    # ---------------- 分发 ----------------
    def dispatch_def(self, a: A.ActorDecl) -> list[str]:
        L = [f"static void D_{a.name}(WhiskerActor* a, void* payload) {{",
             f"{IND}A_{a.name}* self = (A_{a.name}*)a;",
             f"{IND}E_{a.name}* e = (E_{a.name}*)payload;"]
        if a.handlers:
            L.append(f"{IND}switch (e->tag) {{")
            for h in a.handlers:
                args = "".join(f", e->u.h_{h.name}.v_{p.name}" for p in h.params)
                L.append(f"{IND}case T_{a.name}_{h.name}: H_{a.name}_{h.name}(self{args}); break;")
            L.append(f"{IND}default: break;")
            L.append(f"{IND}}}")
        else:
            L.append(f"{IND}(void)self;")
        L.append(f"{IND}whisker_msg_free(e);")
        L.append("}")
        L.append("")
        return L

    # ---------------- 构造 ----------------
    def new_def(self, a: A.ActorDecl) -> list[str]:
        L = [f"static A_{a.name}* N_{a.name}(void) {{",
             f"{IND}A_{a.name}* a = (A_{a.name}*)whisker_actor_new({c_string(a.name)}, "
             f"sizeof(A_{a.name}), D_{a.name});"]
        for f in a.fields:
            init = "NULL" if f.init is None else self.expr(f.init)
            L.append(f"{IND}a->v_{f.name} = {init};")
        L.append(f"{IND}return a;")
        L.append("}")
        L.append("")
        return L

    # ---------------- main ----------------
    def main_def(self) -> list[str]:
        L = ["int main(void) {",
             f"{IND}whisker_runtime_init({self.workers});",
             f"{IND}{{",
             f"{IND}{IND}A_{self.entry_actor}* root = N_{self.entry_actor}();",
             f"{IND}{IND}E_{self.entry_actor}* m = (E_{self.entry_actor}*)whisker_msg_new(sizeof(E_{self.entry_actor}));",
             f"{IND}{IND}m->tag = T_{self.entry_actor}_{self.entry_msg};",
             f"{IND}{IND}whisker_send((WhiskerActor*)root, m);",
             f"{IND}}}",
             f"{IND}whisker_sched_run();",
             f"{IND}whisker_runtime_shutdown();",
             f"{IND}return 0;",
             "}"]
        return L

    # ---------------- 语句 ----------------
    def stmts(self, body: list[A.Stmt], ind: str) -> list[str]:
        L: list[str] = []
        for s in body:
            L += self.stmt(s, ind)
        return L

    def stmt(self, s: A.Stmt, ind: str) -> list[str]:
        if isinstance(s, A.VarStmt):
            self.locals.add(s.name)          # 登记，避免后续赋值重复声明
            if s.init is not None:
                return [f"{ind}{s.ty.c_type()} v_{s.name} = {self.expr(s.init)};"]
            zero = {"Str": '""', "Int": "0", "Bool": "false"}.get(s.ty.kind, "NULL")
            return [f"{ind}{s.ty.c_type()} v_{s.name} = {zero};"]

        if isinstance(s, A.AssignStmt):
            target = s.target
            assert isinstance(target, A.Ident) and target.ref is not None
            kind, name = target.ref
            if kind == "field":
                lhs = f"self->v_{name}"
            else:
                # 第一次赋值 → 就地声明（隐式局部变量）
                decl = "" if name in self.locals else f"{target.ty.c_type()} "
                self.locals.add(name)
                lhs = decl + f"v_{name}"
            return [f"{ind}{lhs} = {self.expr(s.value)};"]

        if isinstance(s, A.ExprStmt):
            e = s.expr
            if isinstance(e, A.SendExpr):
                return self.send(e, ind)
            if isinstance(e, A.Call):
                if e.name == "print":
                    return self.print_call(e, ind)
                return [f"{ind}(void)({self.expr(e)});"]
            return [f"{ind}(void)({self.expr(e)});"]

        if isinstance(s, A.IfStmt):
            L = [f"{ind}if ({self.expr(s.cond)}) {{"]
            L += self.stmts(s.then_body, ind + IND)
            if s.else_body is None:
                L.append(f"{ind}}}")
            else:
                L.append(f"{ind}}} else {{")
                L += self.stmts(s.else_body, ind + IND)
                L.append(f"{ind}}}")
            return L

        if isinstance(s, A.WhileStmt):
            L = [f"{ind}while ({self.expr(s.cond)}) {{"]
            L += self.stmts(s.body, ind + IND)
            L.append(f"{ind}}}")
            return L

        raise AssertionError(f"未处理的语句 {type(s).__name__}")

    def send(self, e: A.SendExpr, ind: str) -> list[str]:
        self.tmp += 1
        ev = f"_e{self.tmp}"
        env = f"E_{e.target_actor}"
        L = [f"{ind}{{"]
        L.append(f"{ind}{IND}{env}* {ev} = ({env}*)whisker_msg_new(sizeof({env}));")
        L.append(f"{ind}{IND}{ev}->tag = T_{e.target_actor}_{e.msg};")
        if e.handler is not None and e.handler.params:
            for p, arg in zip(e.handler.params, e.args):
                L.append(f"{ind}{IND}{ev}->u.h_{e.msg}.v_{p.name} = {self.expr(arg)};")
        L.append(f"{ind}{IND}whisker_send((WhiskerActor*)({self.expr(e.target)}), {ev});")
        L.append(f"{ind}}}")
        return L

    def print_call(self, call: A.Call, ind: str) -> list[str]:
        L = [f"{ind}whisker_print_begin();"]
        for a in call.args:
            fn = a.ty.print_fn()
            assert fn is not None
            L.append(f"{ind}{fn}({self.expr(a)});")
        L.append(f"{ind}whisker_print_end();")
        return L

    # ---------------- 表达式 ----------------
    def expr(self, e: A.Expr) -> str:
        if isinstance(e, A.IntLit):
            return f"INT64_C({e.value})"
        if isinstance(e, A.BoolLit):
            return "true" if e.value else "false"
        if isinstance(e, A.StrLit):
            return c_string(e.value)
        if isinstance(e, A.Ident):
            assert e.ref is not None
            kind, name = e.ref
            return f"self->v_{name}" if kind == "field" else f"v_{name}"
        if isinstance(e, A.SelfExpr):
            return "((WhiskerActor*)self)"
        if isinstance(e, A.SpawnExpr):
            return f"((WhiskerActor*)N_{e.actor}())"
        if isinstance(e, A.Unary):
            return f"({e.op}{self.expr(e.operand)})"
        if isinstance(e, A.Binary):
            op = {"and": "&&", "or": "||"}.get(e.op, e.op)
            return f"({self.expr(e.left)} {op} {self.expr(e.right)})"
        if isinstance(e, A.Call):
            if e.name == "nowMs":
                return "((int64_t)whisker_now_ms())"
            raise AssertionError(f"函数 {e.name} 不能出现在值位置")
        raise AssertionError(f"表达式 {type(e).__name__} 不能出现在值位置")


def emit_c(program: A.Program, entry_actor: str = "Main", entry_msg: str = "Start",
           workers: int = 0) -> str:
    return CEmitter(program, entry_actor, entry_msg, workers).emit()