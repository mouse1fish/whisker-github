"""Whisker 自有 x86-64 代码生成器（完全不用 C / LLVM）

代码质量策略（M1-c）：
  1. **局部变量放寄存器**：self 常驻 rbx，局部变量优先用 r12/r13/r14/r15/rsi/rdi
     （都是「被调用者保存」寄存器，所以跨函数调用不会丢，调用前后无需搬运）。
     寄存器用完了才落到栈槽。
  2. **算符直接吃操作数**：`i + 1` → `add r12, 1`；`i < n` → `cmp r12, r13`；
     只有一侧是复杂表达式时才退回"算到临时槽"的通用路径。
  3. **常量折叠**：纯字面量的算式在编译期算完，例如 `100 * 1000` → 一个立即数。
  4. 栈槽一律 RSP 相对寻址（偏移只与槽位序号有关），调用点始终保持 16 字节对齐。

调用约定：Win64（rcx/rdx/r8/r9，第 5 个起栈传，32 字节 shadow）。
处理函数与函数签名一致：rcx=self，参数依次在 rdx/r8/r9（最多 3 个）。
"""
from __future__ import annotations

from . import ast_nodes as A
from .asm_x64 import (R8, R9, R10, R11, RAX, RBX, RBP, RCX, RDI, RDX, RSI, RSP,
                      R12, R13, R14, R15, Asm)
from .pe_x64 import PEBuilder
from .runtime_x64 import (ACTOR_HEADER, ENV_LINK, ENV_PARAMS, ENV_TAG, Frame,
                          emit_runtime)
from .typesys import INT_TY

MAX_PARAMS = 3          # rdx / r8 / r9
SELF_REG = RBX          # self 常驻寄存器
LOCAL_REGS = (R12, R13, R14, R15, RSI, RDI)   # 局部变量优先用这些（被调用者保存）


class CodegenError(Exception):
    pass


def _c_div(lhs: int, rhs: int) -> int:
    """向零截断的整除（与硬件 idiv 一致，语言语义按这个来）"""
    if rhs == 0:
        return 0
    q = abs(lhs) // abs(rhs)
    return q if (lhs < 0) == (rhs < 0) else -q


def _c_mod(lhs: int, rhs: int) -> int:
    """向零截断的取余：结果符号跟随被除数"""
    if rhs == 0:
        return 0
    return lhs - _c_div(lhs, rhs) * rhs


def const_int(e: A.Expr) -> int:
    """编译期常量表达式求值（字段初值 / 常量折叠都用它）"""
    if isinstance(e, A.IntLit):
        return e.value
    if isinstance(e, A.BoolLit):
        return 1 if e.value else 0
    if isinstance(e, A.Unary):
        v = const_int(e.operand)
        if e.op == "-":
            return -v
        if e.op == "!":
            return 0 if v else 1
        raise CodegenError(e.op)
    if isinstance(e, A.Binary):
        lhs, rhs = const_int(e.left), const_int(e.right)
        op = e.op
        if op == "+":
            return lhs + rhs
        if op == "-":
            return lhs - rhs
        if op == "*":
            return lhs * rhs
        if op == "/":
            return _c_div(lhs, rhs)
        if op == "%":
            return _c_mod(lhs, rhs)
        if op == "==":
            return 1 if lhs == rhs else 0
        if op == "!=":
            return 1 if lhs != rhs else 0
        if op == "<":
            return 1 if lhs < rhs else 0
        if op == "<=":
            return 1 if lhs <= rhs else 0
        if op == ">":
            return 1 if lhs > rhs else 0
        if op == ">=":
            return 1 if lhs >= rhs else 0
        if op in ("&&", "and"):
            return 1 if (lhs and rhs) else 0
        if op in ("||", "or"):
            return 1 if (lhs or rhs) else 0
        raise CodegenError(op)
    raise CodegenError(f"非常量表达式 {type(e).__name__}")


def try_const(e: A.Expr) -> int | None:
    try:
        return const_int(e)
    except CodegenError:
        return None


def is_pure(e: A.Expr) -> bool:
    """表达式是否有副作用（纯表达式才能做公共子表达式消除）"""
    if isinstance(e, (A.IntLit, A.BoolLit, A.StrLit, A.Ident, A.SelfExpr)):
        return True
    if isinstance(e, A.Unary):
        return is_pure(e.operand)
    if isinstance(e, A.Binary):
        return is_pure(e.left) and is_pure(e.right)
    return False        # Call / SendExpr / SpawnExpr 都可能有副作用


def struct_eq(a: A.Expr, b: A.Expr) -> bool:
    """两个表达式在语法上是否完全一致"""
    if type(a) is not type(b):
        return False
    if isinstance(a, A.IntLit):
        return a.value == b.value
    if isinstance(a, A.BoolLit):
        return a.value == b.value
    if isinstance(a, A.StrLit):
        return a.value == b.value
    if isinstance(a, A.Ident):
        return a.name == b.name and a.ref == b.ref
    if isinstance(a, A.SelfExpr):
        return True
    if isinstance(a, A.Unary):
        return a.op == b.op and struct_eq(a.operand, b.operand)
    if isinstance(a, A.Binary):
        return a.op == b.op and struct_eq(a.left, b.left) and struct_eq(a.right, b.right)
    return False


CMP_CC = {"==": "e", "!=": "ne", "<": "l", "<=": "le", ">": "g", ">=": "ge"}


def magic_divisor(d: int):
    """把「除以常数 d」变成「乘魔数 + 移位」，避开高延迟的 idiv

    对 0 <= n < 2^64 成立：floor(n/d) == (n + mulhi_u(n, M)) >> l
    返回 (M, l)；d 不在支持范围时返回 None（退回 idiv）。
    """
    if d < 1 or d >= (1 << 31):
        return None
    l = (d - 1).bit_length()                    # ceil(log2(d))，d=1 时为 0
    A = -((-(1 << (64 + l))) // d)              # ceil(2^(64+l) / d)
    M = (A - (1 << 64)) & 0xFFFFFFFFFFFFFFFF
    return (M, l)


def prescan_locals(body: list[A.Stmt], params: list[A.Param]):
    """按出现顺序收集局部变量（名字 + 类型），用于分配寄存器/栈槽"""
    order: list[tuple[str, object]] = []
    known = {p.name for p in params}

    def add(name: str, ty) -> None:
        if name not in known:
            known.add(name)
            order.append((name, ty))

    def walk(stmts: list[A.Stmt]) -> None:
        for s in stmts:
            if isinstance(s, A.VarStmt):
                add(s.name, s.ty)
            elif isinstance(s, A.AssignStmt):
                t = s.target
                if isinstance(t, A.Ident) and t.ref and t.ref[0] == "local":
                    add(t.name, t.ty)
            elif isinstance(s, A.IfStmt):
                walk(s.then_body)
                if s.else_body:
                    walk(s.else_body)
            elif isinstance(s, A.WhileStmt):
                walk(s.body)
            elif isinstance(s, A.ForStmt):
                add(s.name, INT_TY)
                walk(s.body)

    walk(body)
    return order


class X64Program:
    def __init__(self, program: A.Program, entry_actor: str = "Main",
                 entry_msg: str = "Start") -> None:
        self.program = program
        self.entry_actor = entry_actor
        self.entry_msg = entry_msg
        self.actors = {x.name: x for x in program.actors}
        self.a = Asm()
        self.pe = PEBuilder()
        self._strs: dict[int, str] = {}
        self._str_n = 0
        self._label_n = 0

    # ---------- 查询工具 ----------
    def new_label(self, prefix: str = "L") -> str:
        self._label_n += 1
        return f"{prefix}_{self._label_n}"

    def size_of(self, name: str) -> int:
        raw = ACTOR_HEADER + sum(f.ty.byte_size() for f in self.actors[name].fields)
        return (raw + 15) // 16 * 16

    def field_index(self, actor_name: str, fname: str) -> int:
        for i, f in enumerate(self.actors[actor_name].fields):
            if f.name == fname:
                return i
        raise CodegenError(f"{actor_name} 没有字段 {fname}")

    def field_off(self, actor_name: str, fname: str) -> int:
        """字段偏移（数组字段占 8*长度 字节，所以按累计大小算）"""
        off = ACTOR_HEADER
        for f in self.actors[actor_name].fields:
            if f.name == fname:
                return off
            off += f.ty.byte_size()
        raise CodegenError(f"{actor_name} 没有字段 {fname}")

    def tag_of(self, actor_name: str, msg: str) -> int:
        for i, h in enumerate(self.actors[actor_name].handlers):
            if h.name == msg:
                return i + 1
        raise CodegenError(f"{actor_name} 没有消息 {msg}")

    def str_label(self, node: A.StrLit) -> str:
        lab = self._strs.get(id(node))
        if lab is None:
            lab = f"wstr_{self._str_n}"
            self._str_n += 1
            self.pe.rdata_item(lab, node.value.encode("utf-8") + b"\x00", align=1)
            self._strs[id(node)] = lab
        return lab

    # ---------- 顶层 ----------
    def emit(self) -> str:
        """发射全部机器码；返回入口标签（跨段引用由 PE 写出器统一回填）"""
        emit_runtime(self.a, self.pe)
        for actor in self.program.actors:
            for h in actor.handlers:
                Fn(self, actor, h).emit()
            for fn in actor.funcs:
                Fn(self, actor, fn).emit()
        for actor in self.program.actors:
            self.emit_dispatch(actor)
        self.emit_entry()
        return "whisker_entry"

    # ---------- dispatch ----------
    def emit_dispatch(self, actor: A.ActorDecl) -> None:
        a = self.a
        a.note(f"dispatch {actor.name}")
        a.label(f"D_{actor.name}")
        f = Frame(a)
        sl_self = f.alloc()
        sl_env = f.alloc()
        a.mov_mr(RSP, f.disp(sl_self), RCX)
        a.mov_mr(RSP, f.disp(sl_env), RDX)
        if actor.handlers:
            end = self.new_label("disp_end")
            cases = [self.new_label(f"case_{actor.name}_{h.name}") for h in actor.handlers]
            for i, h in enumerate(actor.handlers):
                a.mov_rm(RAX, RSP, f.disp(sl_env))
                a.mov_rm(RAX, RAX, ENV_TAG)
                a.cmp_ri(RAX, i + 1)
                a.jcc("e", cases[i])
            a.jmp(end)
            for i, h in enumerate(actor.handlers):
                a.label(cases[i])
                a.mov_rm(RCX, RSP, f.disp(sl_self))
                arg_regs = [RDX, R8, R9]
                for j in range(len(h.params)):
                    a.mov_rm(RAX, RSP, f.disp(sl_env))
                    a.mov_rm(arg_regs[j], RAX, ENV_PARAMS + 8 * j)
                a.call(f"H_{actor.name}_{h.name}")
                a.jmp(end)
            a.label(end)
        f.close()

    # ---------- 程序入口 ----------
    def emit_entry(self) -> None:
        a = self.a
        a.note("program entry")
        a.label("whisker_entry")
        # 入口处 RSP≡8（call 约定）；ABI 要求 call 前 RSP≡0。
        # entry 不会返回（TerminateProcess 结束），直接重对齐 rsp。
        a.and_ri(RSP, -16)
        a.call("rt_init")

        entry = self.actors[self.entry_actor]
        a.lea_rip_code(RCX, f"D_{entry.name}")
        a.mov_ri(RDX, self.size_of(entry.name))
        a.call("rt_actor_new")
        a.mov_rip_r("g_entry_actor", RAX)
        self.init_fields(a, entry)          # RAX = actor（期间没有调用，安全）

        a.mov_ri(RCX, ENV_PARAMS)
        a.call("rt_alloc")
        a.mov_mi(RAX, ENV_TAG, self.tag_of(self.entry_actor, self.entry_msg))
        a.mov_mi(RAX, ENV_LINK, 0)
        a.mov_rr(RDX, RAX)
        a.mov_r_rip(RCX, "g_entry_actor")
        a.call("rt_send")

        a.call("rt_run")
        # 用 TerminateProcess 退出：跳过所有 DLL_PROCESS_DETACH 回调。
        # ExitProcess 会跑注入 DLL 的 detach 钩子，在某些环境下（stdout 为管道时）
        # 触发 ole32 崩溃（0xC0000005），TerminateProcess 无此问题。
        a.mov_ri(RCX, -1 & 0xFFFFFFFFFFFFFFFF)   # 伪句柄 = 当前进程
        a.mov_ri(RDX, 0)                          # 退出码
        a.call_rip("imp_TerminateProcess")

    def init_fields(self, a: Asm, actor: A.ActorDecl) -> None:
        """把 actor 字段初值写进 RAX 指向的对象（只允许常量表达式）"""
        for f in actor.fields:
            off = self.field_off(actor.name, f.name)
            if f.init is None:
                continue                    # ActorRef 字段：新分配内存已零化
            if isinstance(f.init, A.StrLit):
                a.lea_rip(RCX, self.str_label(f.init))
                a.mov_mr(RAX, off, RCX)
            else:
                a.mov_mi(RAX, off, const_int(f.init))


class Fn:
    """一个处理函数 / 函数的代码生成上下文"""

    def __init__(self, prog: X64Program, actor: A.ActorDecl, owner) -> None:
        self.p = prog
        self.a = prog.a
        self.actor = actor
        self.owner = owner                  # A.HandlerDecl 或 A.FuncDecl
        self.f: Frame | None = None
        self.loc: dict[str, tuple[str, int]] = {}    # 名字 -> ('reg', 寄存器) / ('slot', 槽位)
        self.loops: list[tuple[str, str]] = []       # (continue 标签, break 标签)
        self.ret_label = ""

    @property
    def label(self) -> str:
        if isinstance(self.owner, A.FuncDecl):
            return f"F_{self.actor.name}_{self.owner.name}"
        return f"H_{self.actor.name}_{self.owner.name}"

    # ---------- 局部变量存取 ----------
    def load_local(self, name: str, dst: int = RAX) -> None:
        kind, val, _ty = self.loc[name]
        if kind == "reg":
            if dst != val:
                self.a.mov_rr(dst, val)
        else:
            self.a.mov_rm(dst, RSP, self.f.disp(val))

    def store_local(self, name: str, src: int = RAX) -> None:
        kind, val, _ty = self.loc[name]
        if kind == "reg":
            if src != val:
                self.a.mov_rr(val, src)
        else:
            self.a.mov_mr(RSP, self.f.disp(val), src)

    # ---------- 数组 ----------
    def array_base(self, e: A.Expr):
        """数组左值的基址：('addr', 基址寄存器, 偏移) 或 ('ptr', 存基址指针的寄存器)"""
        if not isinstance(e, A.Ident) or e.ref is None:
            raise CodegenError("只支持对数组变量/字段/参数做下标访问")
        ref = e.ref
        if ref[0] == "field":
            return ("addr", SELF_REG, self.p.field_off(self.actor.name, ref[1]))
        kind, val, _ty = self.loc[ref[1]]
        if kind == "arr":                       # 数组局部：数据就在栈帧里
            return ("addr", RSP, self.f.disp(val))
        if kind == "reg":                       # 数组参数：寄存器里是基址指针
            return ("ptr", val)
        self.a.mov_rm(R10, RSP, self.f.disp(val))
        return ("ptr", R10)

    def array_addr(self, e: A.Expr, dst: int = RAX) -> None:
        """把数组的基地址放进 dst（传给函数/内置时用）"""
        b = self.array_base(e)
        if b[0] == "addr":
            self.a.lea_mem(dst, b[1], b[2])
        else:
            self.a.mov_rr(dst, b[1])

    def bounds_check(self, size: int) -> None:
        """下标在 RAX：越界就报错退出（无符号比较，负数也算越界）"""
        a = self.a
        ok = self.p.new_label("inb")
        a.cmp_ri(RAX, size)
        a.jcc("b", ok)
        a.call("rt_bounds_fail")
        a.label(ok)

    # ---------- 发射 ----------
    def emit(self) -> None:
        a = self.a
        h = self.owner
        kind = "func" if isinstance(h, A.FuncDecl) else "handler"
        a.note(f"{kind} {self.actor.name}.{h.name}")
        a.label(self.label)                 # 标签必须在序言之前
        if len(h.params) > MAX_PARAMS:
            raise CodegenError(
                f"{self.actor.name}.{h.name} 有 {len(h.params)} 个参数，x64 后端目前最多支持 {MAX_PARAMS} 个")

        # 1) 预扫描局部变量：参数优先，然后是声明的变量
        names: list[tuple[str, object, bool]] = [(p.name, p.ty, True) for p in h.params]
        have = {n for n, _t, _p in names}
        for n, ty in prescan_locals(h.body, h.params):
            if n not in have:
                have.add(n)
                names.append((n, ty, False))

        used_regs: list[int] = []
        for name, ty, is_param in names:
            if (not is_param) and ty is not None and getattr(ty, "is_array", False):
                self.loc[name] = ("arr", -1, ty)        # 数组局部：连续槽位
            elif len(used_regs) < len(LOCAL_REGS):
                r = LOCAL_REGS[len(used_regs)]
                used_regs.append(r)
                self.loc[name] = ("reg", r, ty)
            else:
                self.loc[name] = ("slot", -1, ty)

        # 2) 建帧（保存 self 与用到的局部寄存器）
        self.f = Frame(a, saved=(SELF_REG, *used_regs))
        a.mov_rr(SELF_REG, RCX)
        for name, (k, _v, ty) in list(self.loc.items()):
            if k == "slot":
                self.loc[name] = ("slot", self.f.alloc(), ty)
            elif k == "arr":
                base = self.f.alloc()
                for _ in range(max(0, ty.size - 1)):
                    self.f.alloc()              # 数组占连续 N 个槽
                self.loc[name] = ("arr", base, ty)

        # 3) 参数落位
        src_regs = [RDX, R8, R9]
        for i, p in enumerate(h.params):
            self.store_local(p.name, src_regs[i])

        # 4) 语句
        self.ret_label = self.p.new_label("fn_ret")
        for s in h.body:
            self.stmt(s)
        a.label(self.ret_label)             # return 与自然结束都汇到这里
        self.f.close()

    # ---------- 语句 ----------
    def stmt(self, s: A.Stmt) -> None:
        a = self.a

        if isinstance(s, A.VarStmt):
            kind, val, ty = self.loc.get(s.name, (None, None, None))
            if kind == "arr":                   # 数组局部：占连续槽位，声明时清零
                a.lea_mem(RCX, RSP, self.f.disp(val))
                a.mov_ri(RDX, ty.byte_size())
                a.call("rt_zero")
                return
            if s.init is not None:
                self.eval(s.init)
            else:
                self.zero_value(s.ty)
            self.store_local(s.name)
            return

        if isinstance(s, A.AssignStmt) and isinstance(s.target, A.IndexExpr):
            ix = s.target
            t_v = self.temp()
            self.eval(s.value)
            a.mov_mr(RSP, self.f.disp(t_v), RAX)        # 先存值
            base = self.array_base(ix.obj)
            t_b = -1
            if base[0] == "ptr":                        # 基址指针先落槽，避免被下标求值冲掉
                t_b = self.temp()
                a.mov_mr(RSP, self.f.disp(t_b), base[1])
            self.eval(ix.index)                         # 下标 → RAX
            self.bounds_check(ix.arr_ty.size)
            a.mov_rm(RDX, RSP, self.f.disp(t_v))
            if base[0] == "ptr":
                a.mov_rm(R11, RSP, self.f.disp(t_b))
                a.mov_mr_sib(R11, RAX, RDX, 8, 0)
            else:
                a.mov_mr_sib(base[1], RAX, RDX, 8, base[2])
            return

        if isinstance(s, A.AssignStmt):
            target = s.target
            assert isinstance(target, A.Ident) and target.ref is not None
            kind, name = target.ref
            self.eval(s.value)
            if kind == "field":
                a.mov_mr(SELF_REG, self.p.field_off(self.actor.name, name), RAX)
            else:
                self.store_local(name)
            return

        if isinstance(s, A.ExprStmt):
            e = s.expr
            if isinstance(e, A.SendExpr):
                self.send(e)
            elif isinstance(e, A.Call) and e.name == "print" and e.target is None:
                self.print_call(e)
            else:
                self.eval(e)
            return

        if isinstance(s, A.IfStmt):
            else_l = self.p.new_label("else")
            end_l = self.p.new_label("endif")
            self.eval(s.cond)
            a.test_rr(RAX, RAX)
            a.jcc("e", else_l)
            for c in s.then_body:
                self.stmt(c)
            a.jmp(end_l)
            a.label(else_l)
            if s.else_body:
                for c in s.else_body:
                    self.stmt(c)
            a.label(end_l)
            return

        if isinstance(s, A.WhileStmt):
            top = self.p.new_label("while")
            end = self.p.new_label("endwhile")
            self.loops.append((top, end))
            a.label(top)
            self.eval(s.cond)
            a.test_rr(RAX, RAX)
            a.jcc("e", end)
            for c in s.body:
                self.stmt(c)
            a.jmp(top)
            a.label(end)
            self.loops.pop()
            return

        if isinstance(s, A.ForStmt):
            hi_t = self.temp()                  # 上界只求值一次
            self.eval(s.hi)
            a.mov_mr(RSP, self.f.disp(hi_t), RAX)
            self.eval(s.lo)
            self.store_local(s.name)

            top = self.p.new_label("for")
            cont = self.p.new_label("for_cont")
            end = self.p.new_label("endfor")
            self.loops.append((cont, end))

            a.label(top)
            self.load_local(s.name)
            a.mov_rm(RDX, RSP, self.f.disp(hi_t))
            a.cmp_rr(RAX, RDX)
            a.jcc("g" if s.inclusive else "ge", end)
            for c in s.body:
                self.stmt(c)
            a.label(cont)
            self.load_local(s.name)
            a.add_ri(RAX, 1)
            self.store_local(s.name)
            a.jmp(top)
            a.label(end)
            self.loops.pop()
            return

        if isinstance(s, A.ReturnStmt):
            if s.value is not None:
                self.eval(s.value)
            a.jmp(self.ret_label)
            return

        if isinstance(s, A.BreakStmt):
            a.jmp(self.loops[-1][1])
            return

        if isinstance(s, A.ContinueStmt):
            a.jmp(self.loops[-1][0])
            return

        raise CodegenError(f"未处理的语句 {type(s).__name__}")

    # ---------- 发送消息 ----------
    def send(self, e: A.SendExpr) -> None:
        a = self.a
        size = ENV_PARAMS + 8 * len(e.args)
        a.mov_ri(RCX, size)
        a.call("rt_alloc")
        env = self.temp()
        a.mov_mr(RSP, self.f.disp(env), RAX)
        a.mov_mi(RAX, ENV_TAG, self.p.tag_of(e.target_actor, e.msg))
        a.mov_mi(RAX, ENV_LINK, 0)
        for i, arg in enumerate(e.args):
            self.eval(arg)
            a.mov_rm(RDX, RSP, self.f.disp(env))
            a.mov_mr(RDX, ENV_PARAMS + 8 * i, RAX)
        self.eval(e.target)
        a.mov_rm(RDX, RSP, self.f.disp(env))
        a.mov_rr(RCX, RAX)
        a.call("rt_send")

    # ---------- print ----------
    def print_call(self, call: A.Call) -> None:
        a = self.a
        a.call("rt_print_begin")
        fns = {"Int": "rt_print_int", "Bool": "rt_print_bool", "Str": "rt_print_cstr"}
        for arg in call.args:
            self.eval(arg)
            a.mov_rr(RCX, RAX)
            a.call(fns[arg.ty.kind])
        a.call("rt_print_end")

    # ---------- 辅助 ----------
    def temp(self) -> int:
        return self.f.alloc()

    def zero_value(self, ty) -> None:
        a = self.a
        if ty.kind == "Str":
            a.lea_rip(RAX, "str_empty")
        else:
            a.mov_ri(RAX, 0)                    # Int/Bool/ActorRef 的零值都是 0

    def simple_operand(self, e: A.Expr):
        """能直接当指令操作数用的表达式 → ('imm', v) / ('reg', r) / ('mem', base, disp)"""
        if isinstance(e, A.IntLit):
            if -0x80000000 <= e.value <= 0x7FFFFFFF:
                return ("imm", e.value)
            return None
        if isinstance(e, A.BoolLit):
            return ("imm", 1 if e.value else 0)
        if isinstance(e, A.SelfExpr):
            return ("reg", SELF_REG)
        if isinstance(e, A.Ident):
            ref = e.ref
            if ref is None:
                return None
            if ref[0] == "field":
                f = self.p.actors[self.actor.name]
                return None if self._field_is_array(f, ref[1]) else ("mem", SELF_REG, self.p.field_off(self.actor.name, ref[1]))
            kind, val, ty = self.loc.get(ref[1], ("none", 0, None))
            if ty is not None and getattr(ty, "is_array", False):
                return None                     # 数组不是标量操作数
            if kind == "reg":
                return ("reg", val)
            if kind == "slot":
                return ("mem", RSP, self.f.disp(val))
        return None

    def _field_is_array(self, actor: A.ActorDecl, fname: str) -> bool:
        for f in actor.fields:
            if f.name == fname:
                return bool(f.ty is not None and f.ty.is_array)
        return False

    def apply_binop(self, op: str, rhs) -> None:
        """把二元运算直接作用在 RAX 上（rhs 是 simple_operand 的结果）"""
        a = self.a
        kind = rhs[0]
        val = rhs[1]

        if op == "+":
            if kind == "imm":
                a.add_ri(RAX, val)
            elif kind == "reg":
                a.add_rr(RAX, val)
            else:
                a.add_rm(RAX, val, rhs[2])
        elif op == "-":
            if kind == "imm":
                a.sub_ri(RAX, val)
            elif kind == "reg":
                a.sub_rr(RAX, val)
            else:
                a.sub_rm(RAX, val, rhs[2])
        elif op == "*":
            if kind == "imm":
                a.imul_ri(RAX, val)
            elif kind == "reg":
                a.imul_rr(RAX, val)
            else:
                a.imul_rm(RAX, val, rhs[2])
        elif op in ("/", "%"):
            # 除以常数：用「乘魔数 + 移位」代替 idiv（快 5~8 倍）；负数走慢路径
            if kind == "imm" and val >= 1:
                if val == 1:
                    if op == "%":
                        a.mov_ri(RAX, 0)        # n % 1 恒为 0；n / 1 就是 n 本身
                    return
                mg = magic_divisor(val)
                if mg is not None:
                    M, l = mg
                    done = self.p.new_label("divmod_done")
                    slow = self.p.new_label("divmod_slow")
                    a.mov_rr(R11, RAX)          # 保存 n
                    a.test_rr(RAX, RAX)
                    a.jcc("s", slow)            # 负数：idiv 保正确性
                    a.mov_ri(R10, M)
                    a.mul_r(R10)                # rdx = mulhi_u(n, M)
                    a.add_rr(RDX, R11)
                    a.shr_ri(RDX, l)            # rdx = n / d
                    a.mov_rr(RAX, RDX)
                    if op == "%":
                        a.imul_ri(RAX, val)     # q * d
                        a.mov_rr(R10, R11)
                        a.sub_rr(R10, RAX)      # r = n - q*d
                        a.mov_rr(RAX, R10)
                    a.jmp(done)
                    a.label(slow)
                    a.mov_ri(R10, val)
                    a.cqo()
                    a.idiv_r(R10)
                    if op == "%":
                        a.mov_rr(RAX, RDX)
                    a.label(done)
                    return

            # 除数需要单独的寄存器（不能是 rdx/rax：cqo/idiv 要用它们）
            if kind == "reg" and val not in (RDX, RAX):
                d = val
            else:
                if kind == "imm":
                    a.mov_ri(R10, val)
                elif kind == "reg":
                    a.mov_rr(R10, val)
                else:
                    a.mov_rm(R10, val, rhs[2])
                d = R10
            a.cqo()
            a.idiv_r(d)
            if op == "%":
                a.mov_rr(RAX, RDX)
        elif op in CMP_CC:
            if kind == "imm":
                a.cmp_ri(RAX, val)
            elif kind == "reg":
                a.cmp_rr(RAX, val)
            else:
                a.cmp_rm(RAX, val, rhs[2])
            a.setcc_al(CMP_CC[op])
            a.movzx_eax_al()
        else:
            raise CodegenError(f"未处理的运算符 {op}")

    # ---------- 表达式（结果在 RAX） ----------
    def eval(self, e: A.Expr) -> None:
        a = self.a

        if isinstance(e, A.IntLit):
            a.mov_ri(RAX, e.value)
            return
        if isinstance(e, A.BoolLit):
            a.mov_ri(RAX, 1 if e.value else 0)
            return
        if isinstance(e, A.StrLit):
            a.lea_rip(RAX, self.p.str_label(e))
            return

        if isinstance(e, A.Ident):
            ref = e.ref if e.ref else ("field", e.name)
            if ref[0] == "field":
                a.mov_rm(RAX, SELF_REG, self.p.field_off(self.actor.name, ref[1]))
            else:
                self.load_local(ref[1])
            return

        if isinstance(e, A.SelfExpr):
            a.mov_rr(RAX, SELF_REG)
            return

        if isinstance(e, A.SpawnExpr):
            a.lea_rip_code(RCX, f"D_{e.actor}")
            a.mov_ri(RDX, self.p.size_of(e.actor))
            a.call("rt_actor_new")
            self.p.init_fields(a, self.p.actors[e.actor])
            return

        if isinstance(e, A.Unary):
            self.eval(e.operand)
            if e.op == "-":
                a.neg_r(RAX)
            elif e.op == "!":
                a.test_rr(RAX, RAX)
                a.setcc_al("e")
                a.movzx_eax_al()
            return

        if isinstance(e, A.Binary):
            self.binary(e)
            return

        if isinstance(e, A.IndexExpr):
            base = self.array_base(e.obj)
            b = self.a
            if base[0] == "ptr":                # 基址指针先落槽
                t_b = self.temp()
                b.mov_mr(RSP, self.f.disp(t_b), base[1])
                self.eval(e.index)
                self.bounds_check(e.arr_ty.size)
                b.mov_rm(R11, RSP, self.f.disp(t_b))
                b.mov_rm_sib(RAX, R11, RAX, 8, 0)
            else:
                self.eval(e.index)
                self.bounds_check(e.arr_ty.size)
                b.mov_rm_sib(RAX, base[1], RAX, 8, base[2])
            return

        if isinstance(e, A.Call):
            fn = e.target
            if fn is not None:                  # 本 actor 里 def 声明的函数
                if len(e.args) > MAX_PARAMS:
                    raise CodegenError(
                        f"函数 {fn.name} 调用时参数超过 {MAX_PARAMS} 个，x64 后端暂不支持")
                temps = []
                for arg in e.args:              # 先把实参都算到临时槽，避免互相覆盖
                    if arg.ty is not None and arg.ty.is_array:
                        self.array_addr(arg)    # 数组按引用传：传基地址
                    else:
                        self.eval(arg)
                    t = self.temp()
                    a.mov_mr(RSP, self.f.disp(t), RAX)
                    temps.append(t)
                a.mov_rr(RCX, SELF_REG)
                arg_regs = [RDX, R8, R9]
                for i, t in enumerate(temps):
                    a.mov_rm(arg_regs[i], RSP, self.f.disp(t))
                a.call(f"F_{self.actor.name}_{fn.name}")
                return
            if e.name in ("readFile", "writeFile"):
                temps = []
                for arg in e.args:
                    if arg.ty is not None and arg.ty.is_array:
                        self.array_addr(arg)
                    else:
                        self.eval(arg)
                    t = self.temp()
                    a.mov_mr(RSP, self.f.disp(t), RAX)
                    temps.append(t)
                a.mov_rm(RCX, RSP, self.f.disp(temps[0]))    # 路径
                a.mov_rm(RDX, RSP, self.f.disp(temps[1]))    # 缓冲区
                a.mov_rm(R8, RSP, self.f.disp(temps[2]))     # 字节数
                a.call("rt_read_file" if e.name == "readFile" else "rt_write_file")
                return
            if e.name in ("alloc", "ptrAdd", "load8", "load64", "isNull", "store8",
                          "store64", "copyBytes", "strLen", "strCat", "intToStr",
                          "readBytes", "writeBytes", "strPtr", "ptrToStr", "strToInt"):
                self.builtin_call(e)
                return
            if e.name == "nowMs":
                a.call("rt_now_ms")
                return
            raise CodegenError(f"函数 {e.name} 不能出现在值位置")

    def eval_to_temp(self, arg: A.Expr, by_ref: bool = False) -> int:
        """实参求值进临时槽；数组按引用（传基地址）"""
        if by_ref:
            self.array_addr(arg)
        else:
            self.eval(arg)
        t = self.temp()
        self.a.mov_mr(RSP, self.f.disp(t), RAX)
        return t

    def builtin_call(self, e: A.Call) -> None:
        a = self.a
        name = e.name

        if name == "alloc":                     # alloc(字节数) -> Ptr
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_alloc")
            return

        if name == "ptrAdd":                    # ptrAdd(p, off) -> Ptr
            self.eval(e.args[0])
            t = self.temp()
            a.mov_mr(RSP, self.f.disp(t), RAX)
            self.eval(e.args[1])                # 偏移 → RAX
            a.mov_rm(R10, RSP, self.f.disp(t))
            a.lea_mem_sib(RAX, R10, RAX, 1, 0)  # rax = p + off（地址先算，再覆盖 rax）
            return

        if name == "load8":                     # 读 1 字节
            self.eval(e.args[0])
            a.movzx_r_from_mem8(RAX, RAX, 0)
            return

        if name == "load64":                    # 读 8 字节
            self.eval(e.args[0])
            a.mov_rm(RAX, RAX, 0)
            return

        if name in ("store8", "store64"):       # 写 1/8 字节
            t = self.temp()
            self.eval(e.args[1])                # 先算值
            a.mov_mr(RSP, self.f.disp(t), RAX)
            self.eval(e.args[0])                # 再算指针
            a.mov_rm(RDX, RSP, self.f.disp(t))
            if name == "store8":
                a.mov_mr8(RAX, 0, RDX)
            else:
                a.mov_mr(RAX, 0, RDX)
            return

        if name == "strPtr" or name == "ptrToStr":
            self.eval(e.args[0])                # Str 和 Ptr 在机器码里是同一个东西：显式桥接，无操作
            return

        if name == "isNull":
            self.eval(e.args[0])
            a.test_rr(RAX, RAX)
            a.setcc_al("e")
            a.movzx_eax_al()
            return

        if name == "copyBytes":                 # copyBytes(dst, src, 字节数)
            t0 = self.eval_to_temp(e.args[0])
            t1 = self.eval_to_temp(e.args[1])
            t2 = self.eval_to_temp(e.args[2])
            a.mov_rm(RCX, RSP, self.f.disp(t0))
            a.mov_rm(RDX, RSP, self.f.disp(t1))
            a.mov_rm(R8, RSP, self.f.disp(t2))
            a.call("rt_copy")
            return

        if name == "strLen":
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_str_len")
            return

        if name == "strCat":
            t0 = self.eval_to_temp(e.args[0])
            t1 = self.eval_to_temp(e.args[1])
            a.mov_rm(RCX, RSP, self.f.disp(t0))
            a.mov_rm(RDX, RSP, self.f.disp(t1))
            a.call("rt_str_cat")
            return

        if name == "intToStr":
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_int_to_str")
            return

        if name == "strToInt":
            self.eval(e.args[0])
            a.mov_rr(RCX, RAX)
            a.call("rt_str_to_int")
            return

        if name in ("readBytes", "writeBytes"):  # (路径, 指针, 字节数)
            t0 = self.eval_to_temp(e.args[0])
            t1 = self.eval_to_temp(e.args[1])
            t2 = self.eval_to_temp(e.args[2])
            a.mov_rm(RCX, RSP, self.f.disp(t0))
            a.mov_rm(RDX, RSP, self.f.disp(t1))
            a.mov_rm(R8, RSP, self.f.disp(t2))
            a.call("rt_read_file" if name == "readBytes" else "rt_write_file")
            return

        raise CodegenError(f"未实现的内置函数 {name}")

        raise CodegenError(f"未处理的表达式 {type(e).__name__}")

    def binary(self, e: A.Binary) -> None:
        a = self.a
        op = e.op

        # 常量折叠：纯字面量算式在编译期算完
        v = try_const(e)
        if v is not None:
            a.mov_ri(RAX, v)
            return

        # 公共子表达式：`x op x` 只算一次（左右完全一样且无副作用）
        if op not in ("&&", "||", "and", "or") and is_pure(e.left) and struct_eq(e.left, e.right):
            if op == "+":
                self.eval(e.left)
                a.add_rr(RAX, RAX)
                return
            if op == "*":
                self.eval(e.left)
                a.imul_rr(RAX, RAX)
                return
            if op == "-":
                a.mov_ri(RAX, 0)                # x - x = 0
                return
            if op in ("==", "<=", ">="):
                a.mov_ri(RAX, 1)
                return
            if op in ("!=", "<", ">"):
                a.mov_ri(RAX, 0)
                return

        if op in ("&&", "||", "and", "or"):
            is_and = op in ("&&", "and")
            short = self.p.new_label("sc")
            end = self.p.new_label("scend")
            self.eval(e.left)
            a.test_rr(RAX, RAX)
            a.jcc("e" if is_and else "ne", short)
            self.eval(e.right)
            a.test_rr(RAX, RAX)
            a.jcc("e" if is_and else "ne", short)
            a.mov_ri(RAX, 1 if is_and else 0)   # and：两边都真；or：两边都假
            a.jmp(end)
            a.label(short)
            a.mov_ri(RAX, 0 if is_and else 1)
            a.label(end)
            return

        # 字符串比较
        if op in ("==", "!=") and e.left.ty.kind == "Str":
            t = self.temp()
            self.eval(e.left)
            a.mov_mr(RSP, self.f.disp(t), RAX)
            self.eval(e.right)
            a.mov_rr(RDX, RAX)
            a.mov_rm(RCX, RSP, self.f.disp(t))
            a.call("rt_str_eq")
            if op == "!=":
                a.test_rr(RAX, RAX)
                a.setcc_al("e")
                a.movzx_eax_al()
            return

        # 快路径：右操作数能直接当指令操作数用
        rhs = self.simple_operand(e.right)
        if rhs is not None:
            self.eval(e.left)
            self.apply_binop(op, rhs)
            return

        # 通用路径：左值算到临时槽，右值算进 RDX
        t = self.temp()
        self.eval(e.left)
        a.mov_mr(RSP, self.f.disp(t), RAX)
        self.eval(e.right)
        a.mov_rr(RDX, RAX)
        a.mov_rm(RAX, RSP, self.f.disp(t))
        self.apply_binop(op, ("reg", RDX))


def emit_x64(program: A.Program, entry_actor: str = "Main", entry_msg: str = "Start"):
    """编译并返回 exe 字节"""
    xp = X64Program(program, entry_actor, entry_msg)
    xp.emit()
    return xp.pe.build(xp.a, xp.a.labels["whisker_entry"])