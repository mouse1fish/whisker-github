# -*- coding: utf-8 -*-
"""最小调试器：断在 selfhost.exe 的 cmp 处（RVA 由命令行给出），打印 RAX/RBP/栈槽。

用法: python tools/dbg_probe.py <exe> <rva_hex> [disp1 disp2]
  在 ImageBase+rva 设 int3，断下后打印 RAX、RBP 和 [rbp+disp1]、[rbp+disp2] 的 qword。
"""
import ctypes, struct, sys
from ctypes import wintypes

k = ctypes.windll.kernel32

DEBUG_ONLY_THIS_PROCESS = 0x00000002
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
EXCEPTION_DEBUG_EVENT = 1
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_PROCESS_DEBUG_EVENT = 5
INFINITE = 0xFFFFFFFF

CONTEXT_BUFSZ = 0x4D0
CONTEXT_FULL = 0x10000B

class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD)] * 1 + [("pad", ctypes.c_byte * (104 - 4))]

class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("dwDebugEventCode", wintypes.DWORD),
                ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD),
                ("pad", wintypes.DWORD),
                ("u", ctypes.c_byte * 200)]

def ctx_get(buf, off):
    return struct.unpack_from("<Q", buf, off)[0]

def main():
    exe = sys.argv[1]
    rva = int(sys.argv[2], 16)
    disp1 = int(sys.argv[3]) if len(sys.argv) > 3 else None
    disp2 = int(sys.argv[4]) if len(sys.argv) > 4 else None
    max_hits = int(sys.argv[5]) if len(sys.argv) > 5 else 1

    si = STARTUPINFO(); si.cb = 104
    pinfo = ctypes.create_string_buffer(24)
    ok = k.CreateProcessW(exe, None, None, None, False, DEBUG_ONLY_THIS_PROCESS,
                          None, None, ctypes.byref(si), pinfo)
    if not ok:
        print("CreateProcess fail", k.GetLastError()); return
    hProc = ctypes.cast(pinfo, ctypes.POINTER(wintypes.HANDLE))[0]
    image_base = None
    orig = None
    hits = 0
    stepping = False
    bp_addr = None

    while True:
        ev = DEBUG_EVENT()
        if not k.WaitForDebugEvent(ctypes.byref(ev), 20000):
            print("== 等待事件超时 =="); break
        code = ev.dwDebugEventCode
        status = DBG_CONTINUE
        if code == CREATE_PROCESS_DEBUG_EVENT:
            image_base = struct.unpack_from("<Q", ev.u, 24)[0]
            print(f"== 进程创建 ImageBase=0x{image_base:X}")
        elif code == EXCEPTION_DEBUG_EVENT:
            exc_code = struct.unpack_from("<I", ev.u, 0)[0]
            exc_addr = struct.unpack_from("<Q", ev.u, 16)[0]
            if exc_code != 0x80000003 and exc_code != 0x80000004:
                ctx = ctypes.create_string_buffer(CONTEXT_BUFSZ)
                struct.pack_into("<I", ctx, 0x30, CONTEXT_FULL)
                hThread = k.OpenThread(0x001FFFFF, False, ev.dwThreadId)
                if hThread:
                    k.GetThreadContext(hThread, ctx)
                    rax = ctx_get(ctx, 0x78); rcx = ctx_get(ctx, 0x80); rdx = ctx_get(ctx, 0x88)
                    rbx = ctx_get(ctx, 0x90); rsp = ctx_get(ctx, 0x98); rbp = ctx_get(ctx, 0xA0)
                    rip = ctx_get(ctx, 0xF8)
                    print(f"   [exc] 0x{exc_code:X} @ 0x{exc_addr:X}")
                    print(f"   RIP=0x{rip:X} RAX={rax} RCX=0x{rcx:X} RDX=0x{rdx:X} RBX=0x{rbx:X} RSP=0x{rsp:X} RBP=0x{rbp:X}")
                    # 尝试读 RCX/RDX 指向的 16 字节
                    for rn, rv in (("RCX", rcx), ("RDX", rdx)):
                        buf = ctypes.create_string_buffer(16)
                        got = ctypes.c_size_t()
                        if k.ReadProcessMemory(hProc, ctypes.c_void_p(rv), buf, 16, ctypes.byref(got)):
                            print(f"   [{rn}] -> {buf.raw[:16]!r}")
                        else:
                            print(f"   [{rn}] -> 读取失败 err={k.GetLastError()}")
                    # 读 [RBX+8] 返回地址……改为：读 actor 字段 count/pi（RBX=actor 基址）
                    # 字段 off：count=1048656, pi=1049240（tkKind/tkText 各 65536*8 之后）
                    ret2 = ctypes.c_uint64()
                    got2 = ctypes.c_size_t()
                    if k.ReadProcessMemory(hProc, ctypes.c_void_p(rbp + 8), ctypes.byref(ret2), 8, ctypes.byref(got2)):
                        print(f"   [RBP+8] 返回地址 = 0x{ret2.value:X}（RVA 0x{ret2.value - 0x140000000:X}）")
                    for nm2, fo in (("count", 1048656), ("pi", 1049240), ("kws_off", 1048664)):
                        v = ctypes.c_uint64()
                        got = ctypes.c_size_t()
                        if k.ReadProcessMemory(hProc, ctypes.c_void_p(rbx + fo), ctypes.byref(v), 8, ctypes.byref(got)):
                            print(f"   actor.{nm2} (rbx+{fo}) = {v.value}")
                        else:
                            print(f"   actor.{nm2} 读取失败")
                    # RSP 附近 0x80 字节 hexdump（看栈槽里的左值/右值，含调用方帧）
                    buf = ctypes.create_string_buffer(0x80)
                    got = ctypes.c_size_t()
                    if k.ReadProcessMemory(hProc, ctypes.c_void_p(rsp), buf, 0x80, ctypes.byref(got)):
                        for q in range(0, 0x80, 8):
                            v = struct.unpack_from("<Q", buf.raw, q)[0]
                            print(f"   [rsp+{q:#04x}] = 0x{v:X} ({v})")
                    k.CloseHandle(hThread)
                else:
                    print(f"   [exc] 0x{exc_code:X} @ 0x{exc_addr:X} (OpenThread 失败)")
            if exc_code == 0x80000003 and not image_base is None and stepping is False and hits < max_hits:
                bp_addr = image_base + rva
                if exc_addr == bp_addr:
                    # 断点命中：采样
                    ctx = ctypes.create_string_buffer(CONTEXT_BUFSZ)
                    struct.pack_into("<I", ctx, 0x30, CONTEXT_FULL)
                    hThread = k.OpenThread(0x001FFFFF, False, ev.dwThreadId)
                    k.GetThreadContext(hThread, ctx)
                    rax = ctx_get(ctx, 0x78); rcx = ctx_get(ctx, 0x80)
                    rdx = ctx_get(ctx, 0x88)
                    rbp = ctx_get(ctx, 0xA0); rip = ctx_get(ctx, 0xF8)
                    rsp = ctx_get(ctx, 0x98)
                    rbx = ctx_get(ctx, 0x90)
                    print(f"== 命中#{hits} RIP=0x{rip:X} RAX={rax} RCX=0x{rcx:X} RDX=0x{rdx:X} RBX=0x{rbx:X} RBP=0x{rbp:X} RSP=0x{rsp:X} (RSP%16={rsp % 16})")
                    v = ctypes.c_uint64()
                    got = ctypes.c_size_t()
                    if k.ReadProcessMemory(hProc, ctypes.c_void_p(rsp), ctypes.byref(v), 8, ctypes.byref(got)):
                        print(f"   [rsp+0] 返回地址 = 0x{v.value:X} (RVA 0x{v.value - 0x140000000:X})")
                    for name, d in (("[rbp%+d]" % disp1, disp1), ("[rbp%+d]" % disp2, disp2)):
                        if d is None: continue
                        v = ctypes.c_uint64()
                        got = ctypes.c_size_t()
                        k.ReadProcessMemory(hProc, ctypes.c_void_p(rbp + d), ctypes.byref(v), 8, ctypes.byref(got))
                        print(f"   {name} = {v.value}")
                    # 读 RCX/RDX 指向的前 8 字节（验证字符串指针可访问性）
                    for rn, rv in (("RCX", rcx), ("RDX", rdx)):
                        buf = ctypes.create_string_buffer(8)
                        got = ctypes.c_size_t()
                        if k.ReadProcessMemory(hProc, ctypes.c_void_p(rv), buf, 8, ctypes.byref(got)):
                            print(f"   [{rn}] -> {buf.raw[:8]!r}")
                        else:
                            print(f"   [{rn}] -> 读取失败 err={k.GetLastError()}")
                    # 恢复原字节、RIP 回退、置单步标志
                    got = ctypes.c_size_t()
                    k.WriteProcessMemory(hProc, ctypes.c_void_p(bp_addr), orig, 1, ctypes.byref(got))
                    k.FlushInstructionCache(hProc, ctypes.c_void_p(bp_addr), 1)
                    efl = struct.unpack_from("<I", ctx, 0x44)[0]
                    struct.pack_into("<I", ctx, 0x44, efl | 0x100)  # TF
                    struct.pack_into("<Q", ctx, 0xF8, rip - 1)
                    k.SetThreadContext(hThread, ctx)
                    k.CloseHandle(hThread)
                    hits += 1
                    stepping = True
                    k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
                    continue
                else:
                    # loader 断点：设 int3
                    if orig is None:
                        orig = ctypes.create_string_buffer(1)
                        got = ctypes.c_size_t()
                        k.ReadProcessMemory(hProc, ctypes.c_void_p(bp_addr), orig, 1, ctypes.byref(got))
                        cc = ctypes.create_string_buffer(b"\xCC", 1)
                        wok = k.WriteProcessMemory(hProc, ctypes.c_void_p(bp_addr), cc, 1, ctypes.byref(got))
                        k.FlushInstructionCache(hProc, ctypes.c_void_p(bp_addr), 1)
                        print(f"== loader 断点，int3 写入 0x{bp_addr:X} ok={wok}")
                    k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
                    continue
            elif exc_code == 0x80000004 and stepping:
                # 单步完成：重装 int3，关闭单步
                ctx = ctypes.create_string_buffer(CONTEXT_BUFSZ)
                struct.pack_into("<I", ctx, 0x30, CONTEXT_FULL)
                hThread = k.OpenThread(0x001FFFFF, False, ev.dwThreadId)
                k.GetThreadContext(hThread, ctx)
                efl = struct.unpack_from("<I", ctx, 0x44)[0]
                struct.pack_into("<I", ctx, 0x44, efl & ~0x100)
                k.SetThreadContext(hThread, ctx)
                k.CloseHandle(hThread)
                if hits < max_hits:
                    cc = ctypes.create_string_buffer(b"\xCC", 1)
                    got = ctypes.c_size_t()
                    k.WriteProcessMemory(hProc, ctypes.c_void_p(bp_addr), cc, 1, ctypes.byref(got))
                    k.FlushInstructionCache(hProc, ctypes.c_void_p(bp_addr), 1)
                stepping = False
                k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
                continue
            else:
                if exc_code == 0x80000003:
                    # loader 断点在 image_base 未知或采样完时：放行
                    k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
                    continue
                status = DBG_EXCEPTION_NOT_HANDLED
        elif code == EXIT_PROCESS_DEBUG_EVENT:
            code_exit = struct.unpack_from("<I", ev.u, 0)[0]
            print(f"== 进程退出 code=0x{code_exit:X}")
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
            break
        k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, status)
    k.TerminateProcess(hProc, 0)
    k.CloseHandle(hProc)

if __name__ == "__main__":
    main()
