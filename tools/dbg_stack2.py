"""管道 stdout + 调试器复现：崩溃时栈回溯。用法: python tools/dbg_stack2.py <exe> [runs]"""
import sys, struct, ctypes
from ctypes import wintypes

k = ctypes.windll.kernel32
k.CreateProcessW.restype = wintypes.BOOL
DEBUG_ONLY_THIS_PROCESS = 0x2
EXCEPTION_DEBUG_EVENT = 1
DBG_CONTINUE = 0x10002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001
CONTEXT_BUFSZ = 1232
CONTEXT_FULL = 0x10000B
STARTF_USESTDHANDLES = 0x100

class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", wintypes.DWORD), ("lpSecurityDescriptor", ctypes.c_void_p), ("bInheritHandle", wintypes.BOOL)]

class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", ctypes.c_wchar_p), ("lpDesktop", ctypes.c_wchar_p),
                ("lpTitle", ctypes.c_wchar_p), ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD), ("dwXCountChars", wintypes.DWORD),
                ("dwYCountChars", wintypes.DWORD), ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD), ("lpReserved2", ctypes.c_void_p),
                ("hStdInput", wintypes.HANDLE), ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]

class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE), ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]

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
    sa = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, True)
    r, w = wintypes.HANDLE(), wintypes.HANDLE()
    if not k.CreatePipe(ctypes.byref(r), ctypes.byref(w), ctypes.byref(sa), 0):
        print("pipe fail"); return
    k.SetHandleInformation(r, 1, 0)
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    si.dwFlags = STARTF_USESTDHANDLES
    si.hStdOutput = w
    si.hStdError = w
    pi = PROCESS_INFORMATION()
    cmd = ctypes.create_unicode_buffer('"%s"' % exe)
    ok = k.CreateProcessW(None, cmd, None, None, True, DEBUG_ONLY_THIS_PROCESS, None, None, ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print("CreateProcess fail", k.GetLastError()); return
    k.CloseHandle(w)
    hproc = pi.hProcess
    mods = None
    while True:
        ev = DEBUG_EVENT()
        if not k.WaitForDebugEvent(ctypes.byref(ev), 20000):
            print("== timeout =="); break
        code = ev.dwDebugEventCode
        if code == 3:
            mods = mods_of(ev.dwProcessId)
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
            continue
        if code == 2:
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
            continue
        if code == 5:
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
                rsp = ctx_get(ctx, 0x98); rcx = ctx_get(ctx, 0x80); rdx = ctx_get(ctx, 0x88); rax = ctx_get(ctx, 0x78)
                print("  RSP=0x%x (%%16=%d) RCX=0x%x RDX=0x%x RAX=0x%x" % (rsp, rsp % 16, rcx, rdx, rax))
                buf = ctypes.create_string_buffer(0x400)
                got = ctypes.c_size_t()
                if k.ReadProcessMemory(hproc, ctypes.c_void_p(rsp), buf, 0x400, ctypes.byref(got)):
                    print("  stack scan:")
                    for i in range(0, 0x400, 8):
                        v = struct.unpack_from("<Q", buf, i)[0]
                        m, o = find_mod(mods, v)
                        if m and o > 0:
                            print("    [rsp+%#04x] = %s+0x%x" % (i, m, o))
                # 读 RIP 处指令字节
                b2 = ctypes.create_string_buffer(16)
                if k.ReadProcessMemory(hproc, ctypes.c_void_p(exc_addr), b2, 16, ctypes.byref(got)):
                    print("  [RIP] = %s" % b2.raw[:16].hex())
                # 读 RCX/RDX 指向的内容
                for rn, rv in (("RCX", rcx), ("RDX", rdx)):
                    b3 = ctypes.create_string_buffer(32)
                    if k.ReadProcessMemory(hproc, ctypes.c_void_p(rv), b3, 32, ctypes.byref(got)):
                        print("  [%s] -> %s" % (rn, b3.raw[:32].hex()))
                k.TerminateProcess(hproc, 1)
                k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
                break
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_EXCEPTION_NOT_HANDLED)
            continue
        k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
    k.CloseHandle(r)
    k.CloseHandle(hproc)

if __name__ == "__main__":
    exe = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    for i in range(n):
        print("run %d:" % (i + 1))
        run(exe)
