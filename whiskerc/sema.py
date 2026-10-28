"""Whisker 语义分析

M0 负责：
  - 声明唯一性、名字解析（参数 > 局部变量 > actor 字段）
  - 静态类型检查（含：发给某个 Actor 的消息必须是它声明的 on 处理，参数类型必须匹配）
  - 发送只能在语句位置；字段初值必须是常量
  - 未使用变量警告
"""
from __future__ import annotations

from . import ast_nodes as A
from .diag import Diag
from .typesys import (BOOL_TY, ERROR_TY, INT_TY, PTR_TY, STR_TY, VOID,
                      VOID_TY, Ty, actorref, array_of, parse_type_name)

ENTRY_ACTOR = "Main"
ENTRY_MSG = "Start"

# 内置函数签名：参数类型 + 返回类型（自举第 5 步要用的原语）
BUILTIN_SIGS: dict[str, tuple[list[Ty], Ty]] = {
    "alloc": ([INT_TY], PTR_TY),                    # 分配一块未清零内存
    "ptrAdd": ([PTR_TY, INT_TY], PTR_TY),           # 指针加偏移
    "load8": ([PTR_TY], INT_TY),                    # 读 1 字节（0..255）
    "store8": ([PTR_TY, INT_TY], VOID_TY),          # 写 1 字节
    "load64": ([PTR_TY], INT_TY),                   # 读 8 字节
    "store64": ([PTR_TY, INT_TY], VOID_TY),         # 写 8 字节
    "copyBytes": ([PTR_TY, PTR_TY, INT_TY], VOID_TY),   # 内存拷贝
    "strLen": ([STR_TY], INT_TY),
    "strCat": ([STR_TY, STR_TY], STR_TY),
    "intToStr": ([INT_TY], STR_TY),
    "strToInt": ([STR_TY], INT_TY),
    "isNull": ([PTR_TY], BOOL_TY),
    "strPtr": ([STR_TY], PTR_TY),                   # Str -> Ptr（机器码层面是空操作）
    "ptrToStr": ([PTR_TY], STR_TY),                 # Ptr -> Str（同上，显式桥接）
    "readBytes": ([STR_TY, PTR_TY, INT_TY], INT_TY),    # 读文件到指针（返回字节数/-1）
    "writeBytes": ([STR_TY, PTR_TY, INT_TY], INT_TY),   # 指针内容写文件（返回字节数/-1）
}


def _ends_with_return(body: list[A.Stmt]) -> bool:
    """粗略判断函数体末尾是否一定 return（只做一层 if/else 的启发式）"""
    if not body:
        return False
    last = body[-1]
    if isinstance(last, A.ReturnStmt):
        return True
    if isinstance(last, A.IfStmt):
        if last.else_body is None:
            return False
        return _ends_with_return(last.then_body) and _ends_with_return(last.else_body)
    return False


class Sema:
    def __init__(self, actors: list[A.ActorDecl], diag: Diag) -> None:
        self.actors_list = actors
        self.actors: dict[str, A.ActorDecl] = {}
        self.diag = diag

        self.cur_actor: A.ActorDecl | None = None
        self.cur_func: A.FuncDecl | None = None
        self.funcs: dict[str, A.FuncDecl] = {}
        self.loop_depth = 0
        self.field_tys: dict[str, Ty] = {}
        self.param_tys: dict[str, Ty] = {}
        self.local_tys: dict[str, Ty] = {}
        self.local_decls: list[tuple[str, A.VarStmt]] = []
        self.decl_used: dict[int, bool] = {}

    # ---------------- 入口 ----------------
    def run(self) -> bool:
        seen: set[str] = set()
        for a in self.actors_list:
            if a.name in seen:
                self.diag.error(a.line, a.col, f"actor {a.name} 重复定义")
                continue
            seen.add(a.name)
            self.actors[a.name] = a

        entry = self.actors.get(ENTRY_ACTOR)
        if entry is None:
            self.diag.error(1, 1, f"缺少入口 actor：必须定义 actor {ENTRY_ACTOR} 并实现 on {ENTRY_MSG}()")
        else:
            h = next((h for h in entry.handlers if h.name == ENTRY_MSG), None)
            if h is None:
                self.diag.error(entry.line, entry.col,
                                f"入口 actor {ENTRY_ACTOR} 缺少 on {ENTRY_MSG}() 消息处理")
            elif h.params:
                self.diag.error(h.line, h.col, f"on {ENTRY_MSG}() 不能带参数（入口消息不带数据）")

        for a in self.actors_list:
            self.declare_actor(a)
        for a in self.actors_list:
            self.check_actor_bodies(a)
        return self.diag.ok()

    # ---------------- 第一趟：建立声明（字段类型 + 消息参数签名） ----------------
    def declare_actor(self, a: A.ActorDecl) -> None:
        self.cur_actor = a
        self.field_tys = {}

        # 字段
        for f in a.fields:
            if f.name in self.field_tys:
                self.diag.error(f.line, f.col, f"actor {a.name} 的字段 {f.name} 重复定义")
                continue
            declared = self.resolve_type_expr(f.type_expr) if f.type_expr else None
            if declared is not None and declared.is_error:
                self.field_tys[f.name] = ERROR_TY
                continue

            # ActorRef / 数组字段：不写初始值（运行时内存已零化）
            if f.init is None:
                if declared is None:
                    self.diag.error(f.line, f.col,
                                    f"字段 {f.name} 既没有类型也没有初始值，无法推断类型")
                    self.field_tys[f.name] = ERROR_TY
                    continue
                if not (declared.is_actorref or declared.is_array or declared.is_ptr):
                    self.diag.error(f.line, f.col,
                                    f"字段 {f.name} 必须给初始值"
                                    f"（只有 ActorRef / Ptr / 数组字段可以留空）")
                    self.field_tys[f.name] = ERROR_TY
                    continue
                f.ty = declared
                self.field_tys[f.name] = declared
                continue

            if declared is not None and declared.is_actorref:
                self.diag.error(f.line, f.col,
                                f"字段 {f.name} 是 ActorRef，不能有初始值；"
                                f"请写 {f.name}: {declared}，然后由 connect 消息赋值")
                self.field_tys[f.name] = ERROR_TY
                continue

            if declared is not None and declared.is_array:
                self.diag.error(f.line, f.col,
                                f"字段 {f.name} 是数组，不能有初始值（内存自动清零）；"
                                f"请写 {f.name}: {declared}")
                self.field_tys[f.name] = ERROR_TY
                continue

            self.check_const_expr(f.init, f"字段 {f.name} 的初始值")
            init_ty = f.init.ty or ERROR_TY
            if declared is None:
                f.ty = init_ty
            elif declared != init_ty and not init_ty.is_error:
                self.diag.error(f.line, f.col,
                                f"字段 {f.name} 声明为 {declared}，但初始值是 {init_ty}")
                f.ty = ERROR_TY
            else:
                f.ty = declared
            self.field_tys[f.name] = f.ty

        # 消息处理函数签名（只登记参数类型，函数体留到第二趟）
        seen_handlers: set[str] = set()
        for h in a.handlers:
            if h.name in seen_handlers:
                self.diag.error(h.line, h.col, f"actor {a.name} 的消息 on {h.name} 重复定义")
                continue
            seen_handlers.add(h.name)
            h.actor = a.name
            seen_params: set[str] = set()
            for p in h.params:
                p.ty = self.resolve_type_expr(p.type_expr)
                if p.name in seen_params:
                    self.diag.error(p.line, p.col, f"参数 {p.name} 重复")
                    continue
                seen_params.add(p.name)

        # def 函数签名（同样先登记，函数体留到第二趟）
        seen_funcs: set[str] = set()
        for fn in a.funcs:
            if fn.name in seen_funcs:
                self.diag.error(fn.line, fn.col, f"actor {a.name} 的函数 {fn.name} 重复定义")
                continue
            seen_funcs.add(fn.name)
            fn.actor = a.name
            for p in fn.params:
                p.ty = self.resolve_type_expr(p.type_expr)
            fn.ret_ty = (self.resolve_type_expr(fn.ret_expr) if fn.ret_expr is not None
                         else VOID_TY)

    # ---------------- 第二趟：检查函数体 ----------------
    def check_actor_bodies(self, a: A.ActorDecl) -> None:
        self.cur_actor = a
        self.field_tys = {f.name: f.ty for f in a.fields if f.ty is not None}
        self.funcs = {fn.name: fn for fn in a.funcs if fn.ret_ty is not None}
        for h in a.handlers:
            if h.actor != a.name:      # 重名被跳过的处理函数不再检查
                continue
            if any(p.ty is None for p in h.params):
                continue
            self.check_handler(h)
        for fn in a.funcs:
            if any(p.ty is None for p in fn.params) or fn.ret_ty is None:
                continue
            self.check_func(fn)

    def check_handler(self, h: A.HandlerDecl) -> None:
        self.cur_func = None
        self.loop_depth = 0
        self.param_tys = {}
        self.local_tys = {}
        self.local_decls = []
        self.decl_used = {}

        for p in h.params:
            if p.name in self.field_tys:
                self.diag.warn(p.line, p.col,
                               f"参数 {p.name} 与 actor 字段同名，处理函数内会遮蔽该字段")
            self.param_tys[p.name] = p.ty

        for s in h.body:
            self.check_stmt(s)

        self.warn_unused_locals()

    def check_func(self, fn: A.FuncDecl) -> None:
        self.cur_func = fn
        self.loop_depth = 0
        self.param_tys = {}
        self.local_tys = {}
        self.local_decls = []
        self.decl_used = {}

        seen: set[str] = set()
        for p in fn.params:
            if p.name in seen:
                self.diag.error(p.line, p.col, f"参数 {p.name} 重复")
                continue
            seen.add(p.name)
            self.param_tys[p.name] = p.ty

        for s in fn.body:
            self.check_stmt(s)

        self.warn_unused_locals()
        if fn.ret_ty != VOID_TY and not _ends_with_return(fn.body):
            self.diag.warn(fn.line, fn.col,
                           f"函数 {fn.name} 声明返回 {fn.ret_ty}，但函数体末尾可能没有 return")

    def warn_unused_locals(self) -> None:
        for name, decl in self.local_decls:
            if not self.decl_used.get(id(decl), False):
                self.diag.warn(decl.line, decl.col, f"局部变量 {name} 声明后未使用")

    # ---------------- 类型表达式 ----------------
    def resolve_type_expr(self, te: A.TypeExpr) -> Ty:
        base = parse_type_name(te.name, te.arg)
        if base is None:
            self.diag.error(te.line, te.col, f"未知类型 {te.name}")
            return ERROR_TY
        if base.is_actorref and base.arg not in self.actors:
            self.diag.error(te.line, te.col, f"未知 actor：{base.arg}")
            return ERROR_TY
        if te.size is not None:                       # 数组类型：Int[4096]
            if base.kind == VOID:
                self.diag.error(te.line, te.col, "Void 不能作为数组元素")
                return ERROR_TY
            return array_of(base, te.size)
        return base

    # ---------------- 语句 ----------------
    def check_stmt(self, s: A.Stmt) -> None:
        if isinstance(s, A.VarStmt):
            declared = self.resolve_type_expr(s.type_expr) if s.type_expr else None
            if s.init is None:
                # 只声明不给初值：必须有类型，局部变量取该类型的零值（数组整体清零）
                if declared is None:
                    self.diag.error(s.line, s.col, f"变量 {s.name} 既没有类型也没有初始值")
                    s.ty = ERROR_TY
                else:
                    s.ty = declared
                self.local_tys[s.name] = s.ty
                self.local_decls.append((s.name, s))
                return
            init_ty = self.check_expr(s.init)
            if declared is not None and declared.is_array:
                self.diag.error(s.line, s.col,
                                f"数组 {s.name} 不能给初始值（自动清零）；请写 {s.name}: {declared}")
                s.ty = ERROR_TY
            elif declared is None and init_ty.is_array:
                self.diag.error(s.line, s.col, f"数组 {s.name} 必须写明类型与长度")
                s.ty = ERROR_TY
            elif declared is None:
                s.ty = init_ty
            elif declared != init_ty and not init_ty.is_error and not declared.is_error:
                self.diag.error(s.line, s.col,
                                f"变量 {s.name} 声明为 {declared}，但初始值是 {init_ty}")
                s.ty = ERROR_TY
            else:
                s.ty = declared
            self.local_tys[s.name] = s.ty
            self.local_decls.append((s.name, s))
            return

        if isinstance(s, A.AssignStmt):
            target = s.target

            # 数组元素赋值：buf[i] = v
            if isinstance(target, A.IndexExpr):
                arr_ty = self.check_expr(target.obj)
                idx_ty = self.check_expr(target.index)
                value_ty = self.check_expr(s.value)
                if not arr_ty.is_error and not arr_ty.is_array:
                    self.diag.error(s.line, s.col,
                                    f"{target.obj.__class__.__name__} 不是数组，不能下标赋值")
                if not idx_ty.is_error and idx_ty != INT_TY:
                    self.diag.error(s.index.line, s.index.col,
                                    f"数组下标必须是 Int，当前是 {idx_ty}")
                if arr_ty.is_array:
                    target.arr_ty = arr_ty
                    target.elem_ty = arr_ty.elem
                    target.ty = arr_ty.elem
                    if (not value_ty.is_error and not arr_ty.elem.is_error
                            and value_ty != arr_ty.elem):
                        self.diag.error(s.line, s.col,
                                        f"数组元素类型是 {arr_ty.elem}，赋值的是 {value_ty}")
                return

            if not isinstance(target, A.Ident):
                self.diag.error(s.line, s.col, "赋值目标只能是变量、actor 字段或数组元素")
                self.check_expr(s.value)
                return

            # 名字已存在（参数 / 局部 / 字段）→ 普通赋值
            known = (target.name in self.param_tys or target.name in self.local_tys
                     or target.name in self.field_tys)
            value_ty = self.check_expr(s.value)

            if known:
                ref = self.resolve_ident(target)
                if ref is not None and ref.is_array:
                    self.diag.error(s.line, s.col,
                                    f"数组 {target.name} 不能整体赋值（请逐元素赋值）")
                    return
                if ref is not None and not ref.is_error and not value_ty.is_error and ref != value_ty:
                    self.diag.error(s.line, s.col,
                                    f"赋值类型不匹配：{target.name} 是 {ref}，值是 {value_ty}")
                return

            # 第一次出现这个名字 → 就地声明一个局部变量（Python 味：赋值即诞生）
            if value_ty.is_error:
                target.ref = ("local", target.name)
                target.ty = ERROR_TY
                self.local_tys[target.name] = ERROR_TY
                return
            target.ref = ("local", target.name)
            target.ty = value_ty
            self.local_tys[target.name] = value_ty
            self.local_decls.append((target.name, s))
            return

        if isinstance(s, A.ExprStmt):
            e = s.expr
            if isinstance(e, A.SendExpr):
                self.check_send(e, stmt_position=True)
            elif isinstance(e, A.Call):
                self.check_expr(e)
            else:
                self.diag.error(s.line, s.col,
                                "这句话没有效果：M0 中只有「发送消息」和「print(...)」可以作为独立语句")
                self.check_expr(e)
            return

        if isinstance(s, A.IfStmt):
            cond = self.check_expr(s.cond)
            if not cond.is_error and cond != BOOL_TY:
                self.diag.error(s.cond.line, s.cond.col, f"if 的条件必须是 Bool，当前是 {cond}")
            for c in s.then_body:
                self.check_stmt(c)
            if s.else_body is not None:
                for c in s.else_body:
                    self.check_stmt(c)
            return

        if isinstance(s, A.WhileStmt):
            cond = self.check_expr(s.cond)
            if not cond.is_error and cond != BOOL_TY:
                self.diag.error(s.cond.line, s.cond.col, f"while 的条件必须是 Bool，当前是 {cond}")
            self.loop_depth += 1
            for c in s.body:
                self.check_stmt(c)
            self.loop_depth -= 1
            return

        if isinstance(s, A.ForStmt):
            lo_t = self.check_expr(s.lo)
            hi_t = self.check_expr(s.hi)
            if not lo_t.is_error and lo_t != INT_TY:
                self.diag.error(s.lo.line, s.lo.col, f"for 区间起点必须是 Int，当前是 {lo_t}")
            if not hi_t.is_error and hi_t != INT_TY:
                self.diag.error(s.hi.line, s.hi.col, f"for 区间终点必须是 Int，当前是 {hi_t}")
            self.local_tys[s.name] = INT_TY          # 循环变量是函数级作用域的新局部
            self.local_decls.append((s.name, s))
            self.loop_depth += 1
            for c in s.body:
                self.check_stmt(c)
            self.loop_depth -= 1
            return

        if isinstance(s, A.ReturnStmt):
            if self.cur_func is None:
                if s.value is not None:
                    self.diag.error(s.line, s.col,
                                    "消息处理没有返回类型，return 不能带值（可以只写 return）")
                    self.check_expr(s.value)
                return
            ret = self.cur_func.ret_ty
            s.func = self.cur_func
            if s.value is None:
                if ret != VOID_TY:
                    self.diag.error(s.line, s.col,
                                    f"函数 {self.cur_func.name} 声明返回 {ret}，return 必须带值")
                return
            vt = self.check_expr(s.value)
            s.ty = vt
            if ret == VOID_TY:
                self.diag.error(s.line, s.col,
                                f"函数 {self.cur_func.name} 没有返回类型，return 不能带值")
            elif vt != ret and not vt.is_error:
                self.diag.error(s.line, s.col,
                                f"函数 {self.cur_func.name} 声明返回 {ret}，但这里 return 的是 {vt}")
            return

        if isinstance(s, A.BreakStmt):
            if self.loop_depth == 0:
                self.diag.error(s.line, s.col, "break 只能写在循环里")
            return

        if isinstance(s, A.ContinueStmt):
            if self.loop_depth == 0:
                self.diag.error(s.line, s.col, "continue 只能写在循环里")
            return

    # ---------------- 名字解析 ----------------
    def resolve_ident(self, ident: A.Ident) -> Ty | None:
        name = ident.name
        if name in self.param_tys:
            ident.ref = ("param", name)
            ident.ty = self.param_tys[name]
            return ident.ty
        if name in self.local_tys:
            ident.ref = ("local", name)
            ident.ty = self.local_tys[name]
            for nm, decl in reversed(self.local_decls):
                if nm == name:
                    self.decl_used[id(decl)] = True
                    break
            return ident.ty
        if name in self.field_tys:
            ident.ref = ("field", name)
            ident.ty = self.field_tys[name]
            return ident.ty
        self.diag.error(ident.line, ident.col, f"未定义的标识符 {name}")
        ident.ty = ERROR_TY
        return None

    # ---------------- 常量表达式 ----------------
    def check_const_expr(self, e: A.Expr, what: str) -> None:
        if isinstance(e, (A.IntLit, A.BoolLit, A.StrLit)):
            if isinstance(e, A.IntLit):
                e.ty = INT_TY
            elif isinstance(e, A.BoolLit):
                e.ty = BOOL_TY
            else:
                e.ty = STR_TY
            return
        if isinstance(e, A.Unary):
            self.check_const_expr(e.operand, what)
            e.ty = self.check_unary_ty(e.op, e.operand.ty, e)
            return
        if isinstance(e, A.Binary):
            self.check_const_expr(e.left, what)
            self.check_const_expr(e.right, what)
            e.ty = self.check_binary_ty(e, e.left.ty, e.right.ty)
            return
        self.diag.error(e.line, e.col, f"{what}必须是常量字面量（M0 限制：作用域里还没有 self 和参数）")
        e.ty = ERROR_TY

    # ---------------- 表达式 ----------------
    def check_expr(self, e: A.Expr) -> Ty:
        if isinstance(e, (A.IntLit, A.BoolLit, A.StrLit)):
            e.ty = INT_TY if isinstance(e, A.IntLit) else (BOOL_TY if isinstance(e, A.BoolLit) else STR_TY)
            return e.ty

        if isinstance(e, A.Ident):
            ty = self.resolve_ident(e)
            return ty if ty is not None else ERROR_TY

        if isinstance(e, A.SelfExpr):
            assert self.cur_actor is not None
            e.actor = self.cur_actor.name
            e.ty = actorref(self.cur_actor.name)
            return e.ty

        if isinstance(e, A.SpawnExpr):
            if e.actor not in self.actors:
                self.diag.error(e.line, e.col, f"未知 actor：{e.actor}")
                e.ty = ERROR_TY
            else:
                e.ty = actorref(e.actor)
            return e.ty

        if isinstance(e, A.Unary):
            t = self.check_expr(e.operand)
            e.ty = self.check_unary_ty(e.op, t, e)
            return e.ty

        if isinstance(e, A.Binary):
            lt = self.check_expr(e.left)
            rt = self.check_expr(e.right)
            e.ty = self.check_binary_ty(e, lt, rt)
            return e.ty

        if isinstance(e, A.Call):
            # 1) 本 actor 里 def 声明的函数（可以遮蔽内置名，方便自己实现同名函数）
            fn = self.funcs.get(e.name)
            if fn is not None:
                e.target = fn
                arg_tys = [self.check_expr(a) for a in e.args]
                if len(fn.params) != len(e.args):
                    self.diag.error(e.line, e.col,
                                    f"函数 {e.name} 需要 {len(fn.params)} 个参数，实际给了 {len(e.args)} 个")
                    e.ty = fn.ret_ty
                    return e.ty
                for i, (p, at) in enumerate(zip(fn.params, arg_tys)):
                    if at.is_error or p.ty is None or p.ty.is_error:
                        continue
                    if p.ty != at:
                        self.diag.error(e.args[i].line, e.args[i].col,
                                        f"函数 {e.name} 的第 {i + 1} 个参数 {p.name} 应为 {p.ty}，实际是 {at}")
                e.ty = fn.ret_ty
                return e.ty

            # 2) 内置
            # 2) 内置（带签名的原语）
            sig = BUILTIN_SIGS.get(e.name)
            if sig is not None:
                ptypes, ret = sig
                arg_tys = [self.check_expr(a) for a in e.args]
                if len(arg_tys) != len(ptypes):
                    self.diag.error(e.line, e.col,
                                    f"{e.name} 需要 {len(ptypes)} 个参数，实际给了 {len(arg_tys)} 个")
                else:
                    for i, (want, got) in enumerate(zip(ptypes, arg_tys)):
                        if not got.is_error and got != want:
                            self.diag.error(e.args[i].line, e.args[i].col,
                                            f"{e.name} 的第 {i + 1} 个参数应为 {want}，实际是 {got}")
                e.ty = ret
                return e.ty

            # 3) 内置：文件读写（数组按引用传，第 3 个参数是字节数）
            if e.name in ("readFile", "writeFile"):
                tys = [self.check_expr(a) for a in e.args]
                if len(e.args) != 3:
                    self.diag.error(e.line, e.col,
                                    f"{e.name} 需要 3 个参数（文件路径, 数组, 字节数）")
                else:
                    if not tys[0].is_error and tys[0] != STR_TY:
                        self.diag.error(e.args[0].line, e.args[0].col,
                                        f"{e.name} 第 1 个参数是文件路径（Str），当前是 {tys[0]}")
                    if not tys[1].is_error and not tys[1].is_array:
                        self.diag.error(e.args[1].line, e.args[1].col,
                                        f"{e.name} 第 2 个参数必须是数组，当前是 {tys[1]}")
                    elif tys[1].is_array and tys[1].elem != INT_TY and tys[1].elem != STR_TY:
                        self.diag.error(e.args[1].line, e.args[1].col,
                                        f"{e.name} 只支持 Int[] 或 Str[] 数组，当前是 {tys[1]}")
                    if not tys[2].is_error and tys[2] != INT_TY:
                        self.diag.error(e.args[2].line, e.args[2].col,
                                        f"{e.name} 第 3 个参数是字节数（Int），当前是 {tys[2]}")
                e.ty = INT_TY
                return e.ty

            if e.name == "nowMs":
                for a in e.args:
                    self.check_expr(a)
                if e.args:
                    self.diag.error(e.line, e.col, "nowMs() 不接受参数")
                e.ty = INT_TY
                return e.ty
            if e.name != "print":
                names = "、".join(self.funcs) or "（本 actor 里没有 def 函数）"
                self.diag.error(e.line, e.col,
                                f"未知函数 {e.name}（内置：print / nowMs；可用的自定义函数：{names}）")
                for a in e.args:
                    self.check_expr(a)
                e.ty = ERROR_TY
                return e.ty
            for a in e.args:
                at = self.check_expr(a)
                if at.is_error:
                    continue
                if at.print_fn() is None:
                    self.diag.error(a.line, a.col,
                                    f"print 不支持 {at} 类型（只支持 Int / Bool / Str）")
            e.ty = VOID_TY
            return e.ty

        if isinstance(e, A.IndexExpr):
            arr_ty = self.check_expr(e.obj)
            idx_ty = self.check_expr(e.index)
            if not idx_ty.is_error and idx_ty != INT_TY:
                self.diag.error(e.index.line, e.index.col,
                                f"数组下标必须是 Int，当前是 {idx_ty}")
            if arr_ty.is_error:
                e.ty = ERROR_TY
                return e.ty
            if not arr_ty.is_array:
                self.diag.error(e.line, e.col, f"这个表达式不是数组，不能下标访问（类型是 {arr_ty}）")
                e.ty = ERROR_TY
                return e.ty
            e.arr_ty = arr_ty
            e.elem_ty = arr_ty.elem
            e.ty = arr_ty.elem
            return e.ty

        if isinstance(e, A.SendExpr):
            self.check_send(e, stmt_position=False)
            return e.ty

        raise AssertionError(f"未处理的表达式类型 {type(e).__name__}")

    def check_unary_ty(self, op: str, t: Ty, e: A.Expr) -> Ty:
        if t.is_error:
            return ERROR_TY
        if op == "-":
            if t != INT_TY:
                self.diag.error(e.line, e.col, f"取负只能用于 Int，当前是 {t}")
                return ERROR_TY
            return INT_TY
        if op == "!":
            if t != BOOL_TY:
                self.diag.error(e.line, e.col, f"! 只能用于 Bool，当前是 {t}")
                return ERROR_TY
            return BOOL_TY
        raise AssertionError(op)

    def check_binary_ty(self, e: A.Binary, lt: Ty, rt: Ty) -> Ty:
        if lt.is_error or rt.is_error:
            return ERROR_TY
        op = e.op

        if op in ("+", "-", "*", "/", "%"):
            if lt == INT_TY and rt == INT_TY:
                return INT_TY
            self.diag.error(e.line, e.col, f"运算符 {op} 需要两个 Int，当前是 {lt} 与 {rt}")
            return ERROR_TY

        if op in ("<", "<=", ">", ">="):
            if lt == INT_TY and rt == INT_TY:
                return BOOL_TY
            self.diag.error(e.line, e.col, f"比较运算符 {op} 需要两个 Int，当前是 {lt} 与 {rt}")
            return ERROR_TY

        if op in ("==", "!="):
            if lt == rt and (lt in (INT_TY, BOOL_TY, STR_TY) or lt.is_ptr):
                return BOOL_TY
            self.diag.error(e.line, e.col,
                            f"{op} 只支持 Int/Bool/Str 同类型比较，当前是 {lt} 与 {rt}"
                            + ("（ActorRef 比较在 M1 支持）" if lt.is_actorref or rt.is_actorref else ""))
            return ERROR_TY

        if op in ("&&", "||", "and", "or"):
            if lt == BOOL_TY and rt == BOOL_TY:
                return BOOL_TY
            self.diag.error(e.line, e.col, f"运算符 {op} 需要两个 Bool，当前是 {lt} 与 {rt}")
            return ERROR_TY

        raise AssertionError(op)

    # ---------------- 发送消息 ----------------
    def check_send(self, e: A.SendExpr, stmt_position: bool) -> None:
        e.ty = VOID_TY
        target_ty = self.check_expr(e.target)

        if not stmt_position:
            self.diag.error(e.line, e.col,
                            "发送消息必须作为独立语句（M0 中消息没有返回值）")
        if target_ty.is_error:
            for a in e.args:
                self.check_expr(a)
            return
        if not target_ty.is_actorref:
            self.diag.error(e.line, e.col,
                            f"只有 ActorRef 能发送消息，当前目标类型是 {target_ty}")
            for a in e.args:
                self.check_expr(a)
            return

        actor = self.actors.get(target_ty.arg)
        arg_tys = [self.check_expr(a) for a in e.args]
        if actor is None:
            return   # 已经在类型解析时报过错

        handler = next((h for h in actor.handlers if h.name == e.msg), None)
        if handler is None:
            names = "、".join(h.name for h in actor.handlers) or "（没有）"
            self.diag.error(e.line, e.col,
                            f"actor {actor.name} 没有消息 on {e.msg}（它支持的消息：{names}）")
            return

        params = handler.params
        if len(params) != len(e.args):
            self.diag.error(e.line, e.col,
                            f"消息 {e.msg} 需要 {len(params)} 个参数，实际给了 {len(e.args)} 个")
            return
        for i, (p, at) in enumerate(zip(params, arg_tys)):
            if at.is_error or p.ty is None or p.ty.is_error:
                continue
            if at.is_array or at.is_ptr:
                what = "数组" if at.is_array else "底层指针"
                self.diag.error(e.args[i].line, e.args[i].col,
                                f"{what}不能作为消息发送（Actor 之间只传值；"
                                f"它指向发送方的私有内存，传过去会破坏隔离）")
                continue
            if p.ty != at:
                self.diag.error(e.args[i].line, e.args[i].col,
                                f"消息 {e.msg} 的第 {i + 1} 个参数 {p.name} 应为 {p.ty}，实际是 {at}")
        e.target_actor = actor.name
        e.handler = handler