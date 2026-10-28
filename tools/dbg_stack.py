"""崩溃时栈回溯：扫描栈上的模块内地址，重建调用链。用法: python tools/dbg_stack.py <exe> [runs]"""
import sys, struct, ctypes
from ctypes import wintypes

k = ctypes.windll.kernel32
k.CreateProcessW.restype = wintypes.BOOL
k.WaitForDebugEvent = ctypes.WINFUNCTYPE(wintypes.BOOL, ctypes.c_void_p, wintypes.DWORD)(("WaitForDebugEvent", k))
k.ContinueDebugEvent = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.DWORD, wintypes.DWORD, wintypes.DWORD)(("ContinueDebugEvent", k))
DEBUG_ONLY_THIS_PROCESS = 0x2
EXCEPTION_DEBUG_EVENT = 1
DBG_CONTINUE = 0x10002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
CONTEXT_BUFSZ = 1232
CONTEXT_FULL = 0x10000B

class DEBUG_EVENT(ctypes.Structure):
    _fields_ = [("dwDebugEventCode", wintypes.DWORD),
                ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD),
                ("u", ctypes.c_byte * 200)]

class ME32(ctypes.Structure):
    _fields_ = [("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD),
                ("th32ProcessID", wintypes.DWORD), ("GlblcntUsage", wintypes.DWORD),
                ("ProccntUsage", wintypes.DWORD), ("modBase", ctypes.c_void_p),
                ("modBaseSize", wintypes.DWORD), ("hModule", wintypes.HMODULE),
                ("szModule", ctypes.c_char * 256), ("szExePath", ctypes.c_char * 260)]

def ctx_get(buf, off):
    return struct.unpack_from("<Q", buf, off)[0]

def mods_of(pid):
    snap = k.CreateToolhelp32Snapshot(0x8 | 0x10, pid)
    me = ME32(); me.dwSize = ctypes.sizeof(ME32)
    out = []
    if k.Module32First(snap, ctypes.byref(me)):
        while True:
            out.append((me.szModule.decode(errors="replace"), me.modBase, me.modBaseSize))
            if not k.Module32Next(snap, ctypes.byref(me)):
                break
    k.CloseHandle(snap)
    return out

def find_mod(mods, addr):
    for nm, base, size in mods:
        if base and base <= addr < base + size:
            return nm, addr - base
    return None, None

def run(exe):
    si = ctypes.create_string_buffer(104)
    ctypes.memset(si, 0, 104)
    ctypes.cast(si, ctypes.POINTER(wintypes.DWORD))[0] = 104
    pi = ctypes.create_string_buffer(24)
    ok = k.CreateProcessW(exe, None, None, None, False, DEBUG_ONLY_THIS_PROCESS, None, None, si, pi)
    if not ok:
        print("CreateProcess fail", k.GetLastError()); return
    hproc = ctypes.cast(pi, ctypes.POINTER(wintypes.HANDLE))[0]
    mods = None
    while True:
        ev = DEBUG_EVENT()
        if not k.WaitForDebugEvent(ctypes.byref(ev), 20000):
            print("== timeout =="); break
        code = ev.dwDebugEventCode
        if code == 3:  # CREATE_PROCESS
            mods = mods_of(ev.dwProcessId)
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
            continue
        if code == 2:  # CREATE_THREAD
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
            continue
        if code == 5:  # EXIT_PROCESS
            print("== exit ==")
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
            break
        if code == EXCEPTION_DEBUG_EVENT:
            exc_code = struct.unpack_from("<I", ev.u, 0)[0]
            exc_addr = struct.unpack_from("<Q", ev.u, 16)[0]
            if exc_code == 0xC0000005:
                info = struct.unpack_from("<Q", ev.u, 32)[0]
                target = struct.unpack_from("<Q", ev.u, 40)[0]
                print("AV @0x%x access=%s target=0x%x" % (exc_addr, "read" if info == 0 else "write", target))
                nm, off = find_mod(mods, exc_addr)
                print("  crash in %s+0x%x" % (nm, off) if nm else "  crash addr unknown")
                ctx = ctypes.create_string_buffer(CONTEXT_BUFSZ)
                struct.pack_into("<I", ctx, 0x30, CONTEXT_FULL)
                ht = k.OpenThread(0x001FFFFF, False, ev.dwThreadId)
                k.GetThreadContext(ht, ctypes.byref(ctx))
                rsp = ctx_get(ctx, 0x98)
                print("  RSP=0x%x (%%16=%d)" % (rsp, rsp % 16))
                # 读栈 0x300 字节
                buf = ctypes.create_string_buffer(0x300)
                got = ctypes.c_size_t()
                if k.ReadProcessMemory(hproc, ctypes.c_void_p(rsp), buf, 0x300, ctypes.byref(got)):
                    print("  stack scan (mod-internal qwords):")
                    for i in range(0, 0x300, 8):
                        v = struct.unpack_from("<Q", buf, i)[0]
                        m, o = find_mod(mods, v)
                        if m and o > 0:
                            print("    [rsp+%#04x] = %s+0x%x" % (i, m, o))
                else:
                    print("  stack read fail")
                k.TerminateProcess(hproc, 1)
                k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
                break
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_EXCEPTION_NOT_HANDLED)
            continue
        k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
    k.CloseHandle(hproc)

if __name__ == "__main__":
    exe = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    for i in range(n):
        print("run %d:" % (i + 1))
        run(exe)
