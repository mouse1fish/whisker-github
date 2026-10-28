"""Whisker 自有 x86-64 运行时（用我们自己的机器码编码器生成，不含任何 C 代码）

包含：控制台输出、堆分配（bump + VirtualAlloc 分块）、Actor 邮箱、
**M:N 工作线程调度器（真线程）**、时间戳、字符串比较。

线程模型：
  - 启动时按逻辑核数创建 N 个工作线程，主线程只负责等待系统静止
  - 一把全局自旋锁保护：就绪队列 + Actor 状态 + 邮箱链 + 计数器
  - 消息处理全程在锁外执行 → 多 Actor 真并行
  - 另一把自旋锁保护堆指针（并发分配），第三把保护打印（整条 print 语句原子）

内存与对象布局（生成代码必须一致，集中在这里定义）：

  Actor 头（48 字节）
    +0   dispatch 函数指针        +16  邮箱头
    +8   状态 0 空闲/1 已入队/2 运行中   +24  邮箱尾
    +32  就绪队列 next            +40  保留
  字段区从 +48 起，第 i 个字段在 +48+8i

  消息信封
    +0 tag    +8 邮箱链 next    +16 起载荷，第 i 个参数在 +16+8i
"""
from __future__ import annotations

from .asm_x64 import (R8, R9, R10, R11, RAX, RBP, RCX, RDI, RDX, RSI, RSP, Asm)
from .pe_x64 import PEBuilder

ACTOR_HEADER = 48
ACTOR_DISPATCH = 0
ACTOR_STATE = 8
ACTOR_MBOX_HEAD = 16
ACTOR_MBOX_TAIL = 24
ACTOR_QNEXT = 32

ENV_TAG = 0
ENV_LINK = 8
ENV_PARAMS = 16

HEAP_CHUNK = 0x100000
PRINTBUF_SIZE = 16384
MAX_WORKERS = 64

IMPORTS = ["GetStdHandle", "WriteFile", "VirtualAlloc",
           "QueryPerformanceCounter", "QueryPerformanceFrequency",
           "CreateThread", "GetSystemInfo", "Sleep", "ExitProcess", "TerminateProcess",
           "CreateEventA", "SetEvent", "WaitForSingleObject",
           "CreateFileA", "ReadFile", "CloseHandle"]


def _frame_size(nslots: int, nextra: int = 0) -> int:
    raw = 32 + 8 * nextra + 8 * nslots
    return (raw + 15) // 16 * 16


class Frame:
    """按 Win64 ABI 排布栈帧

    布局（从 rbp 往下）：[被保存的被调用者寄存器][局部槽][栈传参数][shadow 32 字节]
    saved 里的寄存器会被自动压栈/出栈，生成代码因此可以放心把局部变量放在 r12-r15/rsi/rdi 里。
    """

    def __init__(self, a: Asm, nextra: int = 0, saved: tuple[int, ...] = ()) -> None:
        self.a = a
        self.nextra = nextra
        self.saved = list(saved)
        self.nslots = 0
        a.push_r(RBP)
        a.mov_rr(RBP, RSP)
        for r in self.saved:
            a.push_r(r)
        self.patch_off = a.sub_rsp_placeholder()

    def alloc(self) -> int:
        idx = self.nslots
        self.nslots += 1
        return idx

    @property
    def size(self) -> int:
        """帧大小：要装下 shadow + 栈传参数 + 局部槽，并让 rsp 在调用点 16 字节对齐"""
        f = 32 + 8 * self.nextra + 8 * self.nslots
        want = (8 * len(self.saved)) % 16
        while f % 16 != want:
            f += 8
        return f

    def disp(self, idx: int) -> int:
        """槽位相对 RSP 的偏移（只与序号有关，与帧大小无关）"""
        return 32 + 8 * self.nextra + 8 * idx

    def extra_disp(self, i: int) -> int:
        """第 i 个栈传参数相对 RSP 的偏移（Win64：紧跟 shadow 之后）"""
        return 32 + 8 * i

    def close(self) -> None:
        self.a.patch_i32(self.patch_off, self.size)
        if self.saved:
            self.a.lea_mem(RSP, RBP, -8 * len(self.saved))
            for r in reversed(self.saved):
                self.a.pop_r(r)
        else:
            self.a.mov_rr(RSP, RBP)
        self.a.pop_r(RBP)
        self.a.ret()


def emit_runtime(a: Asm, pe: PEBuilder) -> None:
    pe.declare_imports(IMPORTS)

    # ---------------- 全局数据 ----------------
    for g in ("g_stdout", "g_buf_len", "g_heap_ptr", "g_heap_end", "g_qhead", "g_qtail",
              "g_queued", "g_running", "g_shutdown", "g_workers", "g_schedlock",
              "g_heaplock", "g_printlock", "g_freq", "g_t0", "g_now", "g_written",
              "g_entry_actor", "g_thread_ptr", "g_wake", "g_iobytes"):
        pe.data_item(g, b"\x00" * 8)
    pe.data_item("g_scratch", b"\x00" * 32)
    pe.data_item("g_sysinfo", b"\x00" * 48)                       # SYSTEM_INFO
    pe.data_item("g_threads", b"\x00" * (8 * MAX_WORKERS))        # 线程句柄数组
    pe.data_item("g_printbuf", b"\x00" * PRINTBUF_SIZE, align=16)

    pe.rdata_item("str_nl", b"\n")
    pe.rdata_item("str_empty", b"\x00")
    pe.rdata_item("str_oob", "[whisker] 数组越界：程序已终止\n".encode("utf-8") + b"\x00")
    pe.rdata_item("str_minus", b"-")
    pe.rdata_item("str_true", b"true")
    pe.rdata_item("str_false", b"false")

    # ---------------- 自旋锁 ----------------
    # rcx = 锁地址；xchg 带内存操作数隐含 LOCK，天然原子
    a.note("spinlock acquire/release")
    a.label("wsk_lock")
    a.mov_ri(RAX, 1)
    a.label("wsk_lock_retry")
    a.xchg_mr(RCX, 0, RAX)
    a.test_rr(RAX, RAX)
    a.jcc("e", "wsk_lock_done")
    a.pause()
    a.mov_ri(RAX, 1)
    a.jmp("wsk_lock_retry")
    a.label("wsk_lock_done")
    a.ret()

    a.label("wsk_unlock")
    a.mov_mi(RCX, 0, 0)
    a.ret()

    def lock(label: str) -> None:
        a.lea_rip(RCX, label)
        a.call("wsk_lock")

    def unlock(label: str) -> None:
        a.lea_rip(RCX, label)
        a.call("wsk_unlock")

    # ---------------- rt_init ----------------
    a.note("rt_init")
    a.label("rt_init")
    f = Frame(a, nextra=2)                  # CreateThread 有两个栈传参数
    sl_i = f.alloc()
    sl_ptr = f.alloc()
    a.mov_ri(RCX, -11)                      # STD_OUTPUT_HANDLE
    a.call_rip("imp_GetStdHandle")
    a.mov_rip_r("g_stdout", RAX)
    a.lea_rip(RCX, "g_freq")
    a.call_rip("imp_QueryPerformanceFrequency")
    a.lea_rip(RCX, "g_t0")
    a.call_rip("imp_QueryPerformanceCounter")
    a.mov_ri(RCX, 0)
    a.mov_ri(RDX, HEAP_CHUNK)
    a.mov_ri(R8, 0x3000)                    # MEM_COMMIT | MEM_RESERVE
    a.mov_ri(R9, 0x04)                      # PAGE_READWRITE
    a.call_rip("imp_VirtualAlloc")
    a.mov_rip_r("g_heap_ptr", RAX)
    a.mov_rr(RDX, RAX)
    a.add_ri(RDX, HEAP_CHUNK)
    a.mov_rip_r("g_heap_end", RDX)

    # 自动重置事件：入队时唤醒一个空闲工作线程（避免空转烧核）
    a.mov_ri(RCX, 0)                        # lpEventAttributes
    a.mov_ri(RDX, 0)                        # bManualReset = FALSE
    a.mov_ri(R8, 0)                         # bInitialState = FALSE
    a.mov_ri(R9, 0)                         # lpName
    a.call_rip("imp_CreateEventA")
    a.mov_rip_r("g_wake", RAX)

    # 逻辑核数 → 工作线程数
    a.lea_rip(RCX, "g_sysinfo")
    a.call_rip("imp_GetSystemInfo")
    a.lea_rip(RAX, "g_sysinfo")
    a.mov_rm(RAX, RAX, 32)                  # dwNumberOfProcessors
    a.cmp_ri(RAX, 1)
    a.jcc("ge", "rt_init_ge1")
    a.mov_ri(RAX, 1)
    a.label("rt_init_ge1")
    a.cmp_ri(RAX, MAX_WORKERS)
    a.jcc("le", "rt_init_lemax")
    a.mov_ri(RAX, MAX_WORKERS)
    a.label("rt_init_lemax")
    a.mov_rip_r("g_workers", RAX)

    # 创建 N 个工作线程
    a.mov_ri(RCX, 0)
    a.mov_mr(RSP, f.disp(sl_i), RCX)        # i = 0
    a.lea_rip(RCX, "g_threads")
    a.mov_mr(RSP, f.disp(sl_ptr), RCX)      # 句柄数组写指针
    a.label("rt_init_spawn")
    a.mov_rm(RAX, RSP, f.disp(sl_i))
    a.mov_r_rip(RDX, "g_workers")
    a.cmp_rr(RAX, RDX)
    a.jcc("ge", "rt_init_spawned")
    a.mov_ri(RCX, 0)                        # lpThreadAttributes
    a.mov_ri(RDX, 0)                        # dwStackSize
    a.lea_rip_code(R8, "rt_worker")         # lpStartAddress
    a.mov_ri(R9, 0)                         # lpParameter
    a.mov_mi(RSP, f.extra_disp(0), 0)       # dwCreationFlags
    a.mov_mi(RSP, f.extra_disp(1), 0)       # lpThreadId = NULL
    a.call_rip("imp_CreateThread")
    a.mov_rm(RDX, RSP, f.disp(sl_ptr))
    a.mov_mr(RDX, 0, RAX)                   # 记录句柄
    a.add_ri(RDX, 8)
    a.mov_mr(RSP, f.disp(sl_ptr), RDX)
    a.mov_rm(RAX, RSP, f.disp(sl_i))
    a.add_ri(RAX, 1)
    a.mov_mr(RSP, f.disp(sl_i), RAX)
    a.jmp("rt_init_spawn")
    a.label("rt_init_spawned")
    f.close()

    # ---------------- rt_alloc(size) -> rax ----------------
    a.note("rt_alloc")
    a.label("rt_alloc")
    f = Frame(a)
    sl_size = f.alloc()
    sl_chunk = f.alloc()                    # 慢路径用它记住新块大小
    a.mov_mr(RSP, f.disp(sl_size), RCX)
    lock("g_heaplock")
    a.mov_rm(RCX, RSP, f.disp(sl_size))
    a.mov_r_rip(RAX, "g_heap_ptr")
    a.mov_rr(RDX, RAX)
    a.add_rr(RDX, RCX)
    a.mov_r_rip(R8, "g_heap_end")
    a.cmp_rr(RDX, R8)
    a.jcc("be", "rt_alloc_ok")
    a.jmp("rt_alloc_slow")                  # 当前块放不下 → 慢路径（在 rt_alloc_ok 之后）
    # rt_alloc(size)：慢路径（当前块放不下）—— 申请一块「至少 1MB、装得下本次请求」的新块
    a.label("rt_alloc_slow")
    a.mov_rm(RDX, RSP, f.disp(sl_size))
    a.cmp_ri(RDX, HEAP_CHUNK)
    a.jcc("le", "rt_alloc_chunk_ok")
    a.add_ri(RDX, 15)                       # 请求比 1MB 还大：按 16 对齐整块给
    a.and_ri(RDX, -16)
    a.jmp("rt_alloc_have_chunk")
    a.label("rt_alloc_chunk_ok")
    a.mov_ri(RDX, HEAP_CHUNK)
    a.label("rt_alloc_have_chunk")
    a.mov_mr(RSP, f.disp(sl_chunk), RDX)
    a.mov_ri(RCX, 0)
    a.mov_rm(RDX, RSP, f.disp(sl_chunk))
    a.mov_ri(R8, 0x3000)
    a.mov_ri(R9, 0x04)
    a.call_rip("imp_VirtualAlloc")
    a.mov_rr(RDX, RAX)
    a.mov_rm(RCX, RSP, f.disp(sl_chunk))
    a.add_rr(RDX, RCX)
    a.mov_rip_r("g_heap_end", RDX)
    a.mov_rm(RCX, RSP, f.disp(sl_size))
    a.mov_rr(RDX, RAX)
    a.add_rr(RDX, RCX)
    a.mov_rip_r("g_heap_ptr", RDX)
    unlock("g_heaplock")                    # ← 之前漏了这一句：锁没还，下一次分配就死锁
    f.close()

    a.label("rt_alloc_ok")
    a.add_rr(RAX, RCX)
    a.mov_rip_r("g_heap_ptr", RAX)
    a.mov_rr(RAX, RDX)
    a.sub_rr(RAX, RCX)
    unlock("g_heaplock")
    f.close()

    # ---------------- rt_actor_new(rcx=dispatch, rdx=size) -> rax ----------------
    a.note("rt_actor_new")
    a.label("rt_actor_new")
    f = Frame(a)
    sl_d = f.alloc()
    a.mov_mr(RSP, f.disp(sl_d), RCX)
    a.mov_rr(RCX, RDX)
    a.call("rt_alloc")
    a.mov_rm(RCX, RSP, f.disp(sl_d))
    a.mov_mr(RAX, ACTOR_DISPATCH, RCX)
    f.close()

    # ---------------- rt_send(rcx=target, rdx=env) ----------------
    a.note("rt_send")
    a.label("rt_send")
    f = Frame(a)
    sl_t = f.alloc()
    sl_e = f.alloc()
    a.mov_mr(RSP, f.disp(sl_t), RCX)
    a.mov_mr(RSP, f.disp(sl_e), RDX)
    a.mov_mi(RDX, ENV_LINK, 0)              # 信封归我们所有，先接链尾
    lock("g_schedlock")
    a.mov_rm(RCX, RSP, f.disp(sl_t))
    a.mov_rm(RDX, RSP, f.disp(sl_e))
    a.mov_rm(RAX, RCX, ACTOR_MBOX_TAIL)
    a.test_rr(RAX, RAX)
    a.jcc("e", "rt_send_empty")
    a.mov_mr(RAX, ENV_LINK, RDX)
    a.jmp("rt_send_tail")
    a.label("rt_send_empty")
    a.mov_mr(RCX, ACTOR_MBOX_HEAD, RDX)
    a.label("rt_send_tail")
    a.mov_mr(RCX, ACTOR_MBOX_TAIL, RDX)
    a.mov_rm(RAX, RCX, ACTOR_STATE)
    a.test_rr(RAX, RAX)
    a.jcc("ne", "rt_send_done")             # 已在队列/正在运行 → 不必重复入队
    a.mov_mi(RCX, ACTOR_STATE, 1)
    a.mov_r_rip(RAX, "g_qtail")
    a.test_rr(RAX, RAX)
    a.jcc("e", "rt_send_qempty")
    a.mov_mr(RAX, ACTOR_QNEXT, RCX)
    a.jmp("rt_send_qtail")
    a.label("rt_send_qempty")
    a.mov_rip_r("g_qhead", RCX)
    a.label("rt_send_qtail")
    a.mov_rip_r("g_qtail", RCX)
    a.mov_mi(RCX, ACTOR_QNEXT, 0)
    a.mov_r_rip(RAX, "g_queued")
    a.add_ri(RAX, 1)
    a.mov_rip_r("g_queued", RAX)
    a.mov_r_rip(RCX, "g_wake")
    a.call_rip("imp_SetEvent")              # 唤醒一个空闲工作线程
    a.label("rt_send_done")
    unlock("g_schedlock")
    f.close()

    # ---------------- rt_worker：工作线程主体 ----------------
    a.note("rt_worker")
    a.label("rt_worker")
    f = Frame(a)
    sl_actor = f.alloc()
    sl_env = f.alloc()
    sl_next = f.alloc()
    a.label("rt_w_loop")
    lock("g_schedlock")
    a.mov_r_rip(RAX, "g_qhead")
    a.test_rr(RAX, RAX)
    a.jcc("ne", "rt_w_have")
    unlock("g_schedlock")
    a.mov_r_rip(RAX, "g_shutdown")
    a.test_rr(RAX, RAX)
    a.jcc("ne", "rt_w_exit")
    a.mov_r_rip(RCX, "g_wake")
    a.mov_ri(RDX, 10)                       # 最多睡 10ms：空闲零占用，停机也能及时响应
    a.call_rip("imp_WaitForSingleObject")
    a.jmp("rt_w_loop")
    a.label("rt_w_have")
    a.mov_rm(RCX, RAX, ACTOR_QNEXT)
    a.mov_rip_r("g_qhead", RCX)
    a.test_rr(RCX, RCX)
    a.jcc("ne", "rt_w_popq")
    a.xor_rr(RDX, RDX)
    a.mov_rip_r("g_qtail", RDX)
    a.label("rt_w_popq")
    a.mov_r_rip(RCX, "g_queued")
    a.sub_ri(RCX, 1)
    a.mov_rip_r("g_queued", RCX)
    a.mov_mi(RAX, ACTOR_STATE, 2)           # RUNNING
    a.mov_mr(RSP, f.disp(sl_actor), RAX)
    a.mov_rm(RCX, RAX, ACTOR_MBOX_HEAD)     # 整批取走邮箱
    a.mov_mr(RSP, f.disp(sl_env), RCX)
    a.xor_rr(RDX, RDX)
    a.mov_mr(RAX, ACTOR_MBOX_HEAD, RDX)
    a.mov_mr(RAX, ACTOR_MBOX_TAIL, RDX)
    a.mov_r_rip(RDX, "g_running")
    a.add_ri(RDX, 1)
    a.mov_rip_r("g_running", RDX)
    unlock("g_schedlock")

    # 锁外逐个处理（多 Actor 因此真并行）
    a.label("rt_w_batch")
    a.mov_rm(RCX, RSP, f.disp(sl_env))
    a.test_rr(RCX, RCX)
    a.jcc("e", "rt_w_batch_done")
    a.mov_rm(RDX, RCX, ENV_LINK)
    a.mov_mr(RSP, f.disp(sl_next), RDX)
    a.mov_rr(RDX, RCX)                      # 参数：payload
    a.mov_rm(RCX, RSP, f.disp(sl_actor))    # 参数：self
    a.mov_rm(RAX, RCX, ACTOR_DISPATCH)
    a.call_r(RAX)
    a.mov_rm(RAX, RSP, f.disp(sl_next))
    a.mov_mr(RSP, f.disp(sl_env), RAX)
    a.jmp("rt_w_batch")
    a.label("rt_w_batch_done")

    lock("g_schedlock")
    a.mov_r_rip(RDX, "g_running")
    a.sub_ri(RDX, 1)
    a.mov_rip_r("g_running", RDX)
    a.mov_rm(RAX, RSP, f.disp(sl_actor))
    a.mov_rm(RCX, RAX, ACTOR_MBOX_HEAD)
    a.test_rr(RCX, RCX)
    a.jcc("e", "rt_w_idle")
    a.mov_mi(RAX, ACTOR_STATE, 1)           # 处理期间又有新消息 → 重新入队
    a.mov_r_rip(RDX, "g_qtail")
    a.test_rr(RDX, RDX)
    a.jcc("e", "rt_w_q2e")
    a.mov_mr(RDX, ACTOR_QNEXT, RAX)
    a.jmp("rt_w_q2t")
    a.label("rt_w_q2e")
    a.mov_rip_r("g_qhead", RAX)
    a.label("rt_w_q2t")
    a.mov_rip_r("g_qtail", RAX)
    a.mov_mi(RAX, ACTOR_QNEXT, 0)
    a.mov_r_rip(RDX, "g_queued")
    a.add_ri(RDX, 1)
    a.mov_rip_r("g_queued", RDX)
    a.mov_r_rip(RCX, "g_wake")
    a.call_rip("imp_SetEvent")
    a.jmp("rt_w_unlock")
    a.label("rt_w_idle")
    a.mov_mi(RAX, ACTOR_STATE, 0)
    a.label("rt_w_unlock")
    unlock("g_schedlock")
    a.jmp("rt_w_loop")

    a.label("rt_w_exit")
    a.xor_rr(RAX, RAX)
    f.close()

    # ---------------- rt_run：主线程等待系统静止 ----------------
    a.note("rt_run")
    a.label("rt_run")
    f = Frame(a)
    a.label("rt_run_wait")
    lock("g_schedlock")
    a.mov_r_rip(RAX, "g_queued")
    a.mov_r_rip(RDX, "g_running")
    a.or_rr(RAX, RDX)
    unlock("g_schedlock")
    a.test_rr(RAX, RAX)
    a.jcc("e", "rt_run_done")
    a.mov_r_rip(RCX, "g_wake")
    a.mov_ri(RDX, 10)                       # 主线程也睡在事件上：不烧核，静止后 ≤10ms 退出
    a.call_rip("imp_WaitForSingleObject")
    a.jmp("rt_run_wait")
    a.label("rt_run_done")
    sl_wi = f.alloc()
    sl_wp = f.alloc()
    a.mov_ri(RCX, 1)
    a.mov_rip_r("g_shutdown", RCX)          # 通知工作线程退出
    # 唤醒所有空闲 worker（自动重置事件：一次 SetEvent 唤醒一个）
    a.mov_ri(RAX, 0)
    a.mov_mr(RSP, f.disp(sl_wi), RAX)
    a.label("rt_run_wake")
    a.mov_rm(RAX, RSP, f.disp(sl_wi))
    a.mov_r_rip(RDX, "g_workers")
    a.cmp_rr(RAX, RDX)
    a.jcc("ge", "rt_run_join")
    a.mov_r_rip(RCX, "g_wake")
    a.call_rip("imp_SetEvent")
    a.mov_rm(RAX, RSP, f.disp(sl_wi))
    a.add_ri(RAX, 1)
    a.mov_mr(RSP, f.disp(sl_wi), RAX)
    a.jmp("rt_run_wake")
    # 等所有 worker 线程真正退出（5 秒超时兜底：worker 异常时不死锁，
    # 退化为旧行为——由 ExitProcess 强杀）
    a.label("rt_run_join")
    a.lea_rip(RAX, "g_threads")
    a.mov_mr(RSP, f.disp(sl_wp), RAX)
    a.mov_ri(RAX, 0)
    a.mov_mr(RSP, f.disp(sl_wi), RAX)
    a.label("rt_run_join_loop")
    a.mov_rm(RAX, RSP, f.disp(sl_wi))
    a.mov_r_rip(RDX, "g_workers")
    a.cmp_rr(RAX, RDX)
    a.jcc("ge", "rt_run_joined")
    a.mov_rm(RCX, RSP, f.disp(sl_wp))
    a.mov_rm(RCX, RCX, 0)                   # 句柄 = [wp]
    a.mov_ri(RDX, 5000)
    a.call_rip("imp_WaitForSingleObject")
    a.mov_rm(RAX, RSP, f.disp(sl_wp))
    a.add_ri(RAX, 8)
    a.mov_mr(RSP, f.disp(sl_wp), RAX)
    a.mov_rm(RAX, RSP, f.disp(sl_wi))
    a.add_ri(RAX, 1)
    a.mov_mr(RSP, f.disp(sl_wi), RAX)
    a.jmp("rt_run_join_loop")
    a.label("rt_run_joined")
    f.close()

    # ---------------- 输出 ----------------
    a.note("rt_print_begin")
    a.label("rt_print_begin")
    f = Frame(a)
    lock("g_printlock")                     # 整条 print 语句持锁 → 输出不会互相插字
    a.xor_rr(RAX, RAX)
    a.mov_rip_r("g_buf_len", RAX)
    f.close()

    a.label("rt_print_str")                 # rcx=ptr, rdx=len
    f = Frame(a, saved=(RSI, RDI))          # rsi/rdi 是「被调用者保存」：生成代码会拿它们存局部变量
    a.mov_r_rip(RDI, "g_buf_len")
    a.lea_rip(R8, "g_printbuf")
    a.add_rr(RDI, R8)
    a.mov_rr(RSI, RCX)
    a.mov_rr(RCX, RDX)
    a.rep_movsb()
    a.mov_r_rip(RAX, "g_buf_len")
    a.add_rr(RAX, RDX)
    a.mov_rip_r("g_buf_len", RAX)
    f.close()

    a.label("rt_print_cstr")                # rcx=以 0 结尾的字符串
    f = Frame(a)
    sl_p = f.alloc()
    a.mov_mr(RSP, f.disp(sl_p), RCX)
    a.mov_ri(RDX, 0)
    a.label("rt_cstr_loop")
    a.mov_rm(RCX, RSP, f.disp(sl_p))
    a.add_rr(RCX, RDX)
    a.movzx_r_from_mem8(R8, RCX, 0)
    a.test_rr(R8, R8)
    a.jcc("e", "rt_cstr_out")
    a.add_ri(RDX, 1)
    a.jmp("rt_cstr_loop")
    a.label("rt_cstr_out")
    a.mov_rm(RCX, RSP, f.disp(sl_p))
    a.call("rt_print_str")
    f.close()

    a.label("rt_print_int")                 # rcx=值
    f = Frame(a)
    sl_v = f.alloc()
    a.mov_mr(RSP, f.disp(sl_v), RCX)
    a.test_rr(RCX, RCX)
    a.jcc("ns", "rt_int_pos")
    a.lea_rip(RCX, "str_minus")
    a.mov_ri(RDX, 1)
    a.call("rt_print_str")
    a.mov_rm(RAX, RSP, f.disp(sl_v))
    a.neg_r(RAX)
    a.mov_mr(RSP, f.disp(sl_v), RAX)
    a.label("rt_int_pos")
    a.lea_rip(R8, "g_scratch")
    a.add_ri(R8, 32)
    a.mov_ri(R9, 0)
    a.mov_rm(RAX, RSP, f.disp(sl_v))
    a.test_rr(RAX, RAX)
    a.jcc("ne", "rt_int_loop")
    a.sub_ri(R8, 1)
    a.mov_ri(RDX, 48)
    a.mov_mr8(R8, 0, RDX)
    a.mov_ri(R9, 1)
    a.jmp("rt_int_out")
    a.label("rt_int_loop")
    a.xor_rr(RDX, RDX)
    a.mov_ri(R10, 10)
    a.div_r(R10)
    a.add_ri(RDX, 48)
    a.sub_ri(R8, 1)
    a.mov_mr8(R8, 0, RDX)
    a.add_ri(R9, 1)
    a.test_rr(RAX, RAX)
    a.jcc("ne", "rt_int_loop")
    a.label("rt_int_out")
    a.mov_rr(RCX, R8)
    a.mov_rr(RDX, R9)
    a.call("rt_print_str")
    f.close()

    a.label("rt_print_bool")                # rcx=0/1
    f = Frame(a)
    a.test_rr(RCX, RCX)
    a.jcc("e", "rt_bool_false")
    a.lea_rip(RCX, "str_true")
    a.mov_ri(RDX, 4)
    a.call("rt_print_str")
    f.close()
    a.label("rt_bool_false")
    a.lea_rip(RCX, "str_false")
    a.mov_ri(RDX, 5)
    a.call("rt_print_str")
    f.close()

    a.label("rt_print_end")
    f = Frame(a, nextra=1)
    a.lea_rip(RCX, "str_nl")
    a.mov_ri(RDX, 1)
    a.call("rt_print_str")
    a.mov_r_rip(RCX, "g_stdout")
    a.lea_rip(RDX, "g_printbuf")
    a.mov_r_rip(R8, "g_buf_len")
    a.lea_rip(R9, "g_written")
    a.mov_mi(RSP, f.extra_disp(0), 0)       # WriteFile 第 5 个参数（栈传）
    a.call_rip("imp_WriteFile")
    unlock("g_printlock")
    f.close()

    # ---------------- 数组与文件（自举所需的基础设施） ----------------
    a.note("rt_zero / rt_bounds_fail / rt_read_file / rt_write_file")

    # rt_zero(rcx=地址, rdx=字节数)：按 8 字节清零（数组长度都是 8 的倍数）
    a.label("rt_zero")
    a.test_rr(RDX, RDX)
    a.jcc("e", "rt_zero_done")
    a.mov_rr(R8, RDX)
    a.xor_rr(RAX, RAX)
    a.label("rt_zero_loop")
    a.mov_mr(RCX, 0, RAX)
    a.add_ri(RCX, 8)
    a.sub_ri(R8, 8)
    a.jcc("g", "rt_zero_loop")
    a.label("rt_zero_done")
    a.ret()

    # rt_bounds_fail()：数组越界 —— 打印一行并退出（不返回）
    a.label("rt_bounds_fail")
    f = Frame(a)
    a.lea_rip(RCX, "str_oob")
    a.call("rt_print_cstr")
    a.call("rt_print_end")
    a.mov_ri(RCX, -1 & 0xFFFFFFFFFFFFFFFF)   # 伪句柄 = 当前进程（跳过 DLL detach）
    a.mov_ri(RDX, 1)                          # 退出码 1（越界失败）
    a.call_rip("imp_TerminateProcess")
    f.close()

    # rt_read_file(rcx=路径, rdx=缓冲区, r8=最多读多少) -> rax=读到的字节数 / -1
    a.label("rt_read_file")
    f = Frame(a, nextra=3)                  # CreateFileA 有 7 个参数
    sl_h = f.alloc()
    sl_buf = f.alloc()
    sl_max = f.alloc()
    a.mov_mr(RSP, f.disp(sl_buf), RDX)
    a.mov_mr(RSP, f.disp(sl_max), R8)
    a.mov_ri(RDX, 0x80000000)               # GENERIC_READ
    a.mov_ri(R8, 1)                         # FILE_SHARE_READ
    a.mov_ri(R9, 0)                         # lpSecurityAttributes
    a.mov_mi(RSP, f.extra_disp(0), 3)       # OPEN_EXISTING
    a.mov_mi(RSP, f.extra_disp(1), 0x80)    # FILE_ATTRIBUTE_NORMAL
    a.mov_mi(RSP, f.extra_disp(2), 0)       # hTemplateFile
    a.call_rip("imp_CreateFileA")
    a.cmp_ri(RAX, -1)
    a.jcc("ne", "rt_rf_ok")
    a.mov_ri(RAX, -1)
    f.close()
    a.label("rt_rf_ok")
    a.mov_mr(RSP, f.disp(sl_h), RAX)
    a.mov_rr(RCX, RAX)
    a.mov_rm(RDX, RSP, f.disp(sl_buf))
    a.mov_rm(R8, RSP, f.disp(sl_max))
    a.lea_rip(R9, "g_iobytes")
    a.mov_mi(RSP, f.extra_disp(0), 0)       # lpOverlapped = NULL
    a.call_rip("imp_ReadFile")
    a.mov_rm(RCX, RSP, f.disp(sl_h))
    a.call_rip("imp_CloseHandle")
    a.mov_r_rip(RAX, "g_iobytes")
    f.close()

    # rt_write_file(rcx=路径, rdx=缓冲区, r8=字节数) -> rax=写入的字节数 / -1
    a.label("rt_write_file")
    f = Frame(a, nextra=3)
    sl_h = f.alloc()
    sl_buf = f.alloc()
    sl_cnt = f.alloc()
    a.mov_mr(RSP, f.disp(sl_buf), RDX)
    a.mov_mr(RSP, f.disp(sl_cnt), R8)
    a.mov_ri(RDX, 0x40000000)               # GENERIC_WRITE
    a.mov_ri(R8, 1)                         # FILE_SHARE_READ
    a.mov_ri(R9, 0)
    a.mov_mi(RSP, f.extra_disp(0), 2)       # CREATE_ALWAYS
    a.mov_mi(RSP, f.extra_disp(1), 0x80)
    a.mov_mi(RSP, f.extra_disp(2), 0)
    a.call_rip("imp_CreateFileA")
    a.cmp_ri(RAX, -1)
    a.jcc("ne", "rt_wf_ok")
    a.mov_ri(RAX, -1)
    f.close()
    a.label("rt_wf_ok")
    a.mov_mr(RSP, f.disp(sl_h), RAX)
    a.mov_rr(RCX, RAX)
    a.mov_rm(RDX, RSP, f.disp(sl_buf))
    a.mov_rm(R8, RSP, f.disp(sl_cnt))
    a.lea_rip(R9, "g_iobytes")
    a.mov_mi(RSP, f.extra_disp(0), 0)
    a.call_rip("imp_WriteFile")
    a.mov_rm(RCX, RSP, f.disp(sl_h))
    a.call_rip("imp_CloseHandle")
    a.mov_r_rip(RAX, "g_iobytes")
    f.close()

    # ---------------- 字符串与内存（自举第 5 步要用的原语） ----------------
    a.note("rt_str_len / rt_str_cat / rt_int_to_str / rt_copy")

    # rt_str_len(rcx=s) -> rax = 字符串长度（不含结尾 0）
    a.label("rt_str_len")
    f = Frame(a, saved=(RSI,))
    a.mov_rr(RSI, RCX)
    a.xor_rr(RAX, RAX)
    a.label("rt_sl_loop")
    a.movzx_r_from_mem8(R8, RSI, 0)
    a.test_rr(R8, R8)
    a.jcc("e", "rt_sl_done")
    a.add_ri(RAX, 1)
    a.add_ri(RSI, 1)
    a.jmp("rt_sl_loop")
    a.label("rt_sl_done")
    f.close()

    # rt_str_cat(rcx=a, rdx=b) -> rax = 新字符串（a+b，新分配）
    a.label("rt_str_cat")
    f = Frame(a, saved=(RSI, RDI))
    sl_a = f.alloc()
    sl_b = f.alloc()
    sl_la = f.alloc()
    sl_out = f.alloc()
    a.mov_mr(RSP, f.disp(sl_a), RCX)
    a.mov_mr(RSP, f.disp(sl_b), RDX)
    a.mov_rm(RCX, RSP, f.disp(sl_a))
    a.call("rt_str_len")
    a.mov_mr(RSP, f.disp(sl_la), RAX)
    a.mov_rm(RCX, RSP, f.disp(sl_b))
    a.call("rt_str_len")
    a.mov_rm(RDX, RSP, f.disp(sl_la))
    a.add_rr(RAX, RDX)
    a.add_ri(RAX, 1)                         # total = la + lb + 1
    a.mov_rr(RCX, RAX)
    a.call("rt_alloc")                       # rax = 新串
    a.mov_mr(RSP, f.disp(sl_out), RAX)       # ← 记住新串指针（后面 rax 会被用掉）
    a.mov_rr(RDI, RAX)
    a.mov_rm(RSI, RSP, f.disp(sl_a))
    a.mov_rm(RDX, RSP, f.disp(sl_la))
    a.mov_rr(RCX, RDX)
    a.rep_movsb()                            # 拷 a；rdi 自动指到接缝
    a.mov_rm(RSI, RSP, f.disp(sl_b))
    a.mov_rm(RCX, RSP, f.disp(sl_b))
    a.call("rt_str_len")
    a.mov_rr(RCX, RAX)
    a.mov_rm(RSI, RSP, f.disp(sl_b))
    a.rep_movsb()                            # 拷 b
    a.mov_ri(RDX, 0)
    a.mov_mr8(RDI, 0, RDX)                   # 结尾 0
    a.mov_rm(RAX, RSP, f.disp(sl_out))       # 返回新串
    f.close()

    # rt_int_to_str(rcx=n) -> rax = 十进制字符串（新分配）
    a.label("rt_int_to_str")
    f = Frame(a, saved=(RSI, RDI))
    sl_dst = f.alloc()
    sl_n = f.alloc()
    sl_neg = f.alloc()
    sl_digits = f.alloc()
    a.mov_mr(RSP, f.disp(sl_n), RCX)
    a.mov_ri(RCX, 24)
    a.call("rt_alloc")
    a.mov_mr(RSP, f.disp(sl_dst), RAX)

    a.mov_ri(RCX, 0)
    a.mov_mr(RSP, f.disp(sl_neg), RCX)       # 符号标志
    a.mov_rm(RAX, RSP, f.disp(sl_n))
    a.test_rr(RAX, RAX)
    a.jcc("ns", "rt_its_pos")
    a.mov_ri(RCX, 1)
    a.mov_mr(RSP, f.disp(sl_neg), RCX)
    a.neg_r(RAX)
    a.mov_mr(RSP, f.disp(sl_n), RAX)
    a.label("rt_its_pos")

    # 第一遍：数位数
    a.mov_ri(RCX, 0)
    a.mov_rm(R11, RSP, f.disp(sl_n))
    a.test_rr(R11, R11)
    a.jcc("ne", "rt_its_cnt")
    a.mov_ri(RCX, 1)
    a.jmp("rt_its_cnt_done")
    a.label("rt_its_cnt")
    a.add_ri(RCX, 1)
    a.mov_ri(R8, 10)
    a.mov_rr(RAX, R11)
    a.xor_rr(RDX, RDX)
    a.div_r(R8)
    a.mov_rr(R11, RAX)
    a.test_rr(R11, R11)
    a.jcc("ne", "rt_its_cnt")
    a.label("rt_its_cnt_done")
    a.mov_mr(RSP, f.disp(sl_digits), RCX)

    # 第二遍：从末尾往前写数字（0 要特判：写一个 '0'）
    a.mov_rm(RAX, RSP, f.disp(sl_dst))
    a.mov_rm(RCX, RSP, f.disp(sl_digits))
    a.mov_rm(RDX, RSP, f.disp(sl_neg))
    a.add_rr(RCX, RDX)
    a.lea_mem(R10, RAX, 0)
    a.add_rr(R10, RCX)                       # r10 = NUL 的位置
    a.mov_ri(RDX, 0)
    a.mov_mr8(R10, 0, RDX)                   # 写 NUL
    a.mov_rm(R11, RSP, f.disp(sl_n))
    a.test_rr(R11, R11)
    a.jcc("ne", "rt_its_write")
    a.sub_ri(R10, 1)
    a.mov_ri(RDX, 48)
    a.mov_mr8(R10, 0, RDX)                   # n == 0 → 写 '0'
    a.jmp("rt_its_sign")
    a.label("rt_its_write")
    a.test_rr(R11, R11)
    a.jcc("e", "rt_its_sign")
    a.xor_rr(RDX, RDX)
    a.mov_ri(R8, 10)
    a.mov_rr(RAX, R11)
    a.div_r(R8)
    a.add_ri(RDX, 48)
    a.sub_ri(R10, 1)
    a.mov_mr8(R10, 0, RDX)
    a.mov_rr(R11, RAX)
    a.jmp("rt_its_write")
    a.label("rt_its_sign")
    a.mov_rm(RDX, RSP, f.disp(sl_neg))
    a.test_rr(RDX, RDX)
    a.jcc("e", "rt_its_done")
    a.sub_ri(R10, 1)
    a.mov_ri(RDX, 45)
    a.mov_mr8(R10, 0, RDX)
    a.label("rt_its_done")
    a.mov_rm(RAX, RSP, f.disp(sl_dst))
    f.close()

    # rt_str_to_int(rcx=s) -> rax = 十进制整数值（可选负号；token 文本都是干净的）
    a.label("rt_str_to_int")
    f = Frame(a, saved=(RSI,))
    a.mov_rr(RSI, RCX)
    a.mov_ri(RAX, 0)
    a.mov_ri(RCX, 1)                        # 符号
    a.movzx_r_from_mem8(R8, RSI, 0)
    a.cmp_ri(R8, 45)                        # '-'
    a.jcc("ne", "rt_sti_digits")
    a.mov_ri(RCX, -1)
    a.add_ri(RSI, 1)
    a.label("rt_sti_digits")
    a.movzx_r_from_mem8(R8, RSI, 0)
    a.sub_ri(R8, 48)
    a.cmp_ri(R8, 0)
    a.jcc("l", "rt_sti_done")
    a.cmp_ri(R8, 9)
    a.jcc("g", "rt_sti_done")
    a.mov_ri(R9, 10)
    a.mul_r(R9)
    a.add_rr(RAX, R8)
    a.add_ri(RSI, 1)
    a.jmp("rt_sti_digits")
    a.label("rt_sti_done")
    a.imul_rr(RAX, RCX)                     # 乘符号（1 或 -1）
    f.close()
    # rt_copy(rcx=dst, rdx=src, r8=字节数)
    a.label("rt_copy")
    f = Frame(a, saved=(RSI, RDI))
    a.mov_rr(RSI, RDX)
    a.mov_rr(RDI, RCX)
    a.mov_rr(RCX, R8)
    a.rep_movsb()
    f.close()

    # ---------------- 时间 ----------------
    a.note("rt_now_ms")
    a.label("rt_now_ms")
    f = Frame(a)
    a.lea_rip(RCX, "g_now")
    a.call_rip("imp_QueryPerformanceCounter")
    a.mov_r_rip(RAX, "g_now")
    a.mov_r_rip(RCX, "g_t0")
    a.sub_rr(RAX, RCX)
    a.mov_ri(RCX, 1000)
    a.mul_r(RCX)
    a.mov_r_rip(RCX, "g_freq")
    a.div_r(RCX)
    f.close()

    # ---------------- 字符串比较 ----------------
    a.note("rt_str_eq")
    a.label("rt_str_eq")                    # rcx=a, rdx=b -> rax=0/1
    f = Frame(a)
    a.label("rt_seq_loop")
    a.movzx_r_from_mem8(RAX, RCX, 0)
    a.movzx_r_from_mem8(R8, RDX, 0)
    a.cmp_rr(RAX, R8)
    a.jcc("ne", "rt_seq_no")
    a.test_rr(RAX, RAX)
    a.jcc("e", "rt_seq_yes")
    a.add_ri(RCX, 1)
    a.add_ri(RDX, 1)
    a.jmp("rt_seq_loop")
    a.label("rt_seq_no")
    a.xor_rr(RAX, RAX)
    f.close()
    a.label("rt_seq_yes")
    a.mov_ri(RAX, 1)
    f.close()