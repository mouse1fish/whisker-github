"""Mini debugger: run an exe under DEBUG_PROCESS, report first AV with fault address + RVA.
Usage: python tools/dbg_av.py <exe> [runs]
"""
import sys, ctypes, struct as _struct
from ctypes import wintypes


def struct_unpack_q(buf, off):
    return _struct.unpack_from("<Q", buf, off)[0]

k = ctypes.windll.kernel32
k.CreateProcessW.restype = wintypes.BOOL

EXCEPTION_DEBUG_EVENT = 1
CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_PROCESS_DEBUG_EVENT = 5
DBG_CONTINUE = 0x10002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001


class EXCEPTION_RECORD64(ctypes.Structure):
    _fields_ = [("ExceptionCode", wintypes.DWORD), ("ExceptionFlags", wintypes.DWORD),
                ("ExceptionRecord", ctypes.c_uint64), ("ExceptionAddress", ctypes.c_uint64),
                ("NumberParameters", wintypes.DWORD), ("ExceptionInformation", ctypes.c_uint64 * 15)]


class DEBUG_EVENT(ctypes.Structure):
    class U(ctypes.Union):
        class E(ctypes.Structure):
            _fields_ = [("ExceptionRecord", EXCEPTION_RECORD64), ("dwFirstChance", wintypes.DWORD)]
        class C(ctypes.Structure):
            _fields_ = [("hFile", wintypes.HANDLE), ("hProcess", wintypes.HANDLE),
                        ("hThread", wintypes.HANDLE), ("lpBaseOfImage", ctypes.c_void_p),
                        ("dwDebugInfoFileOffset", wintypes.DWORD), ("nDebugInfoSize", wintypes.DWORD),
                        ("lpThreadLocalBase", ctypes.c_void_p), ("lpStartAddress", ctypes.c_void_p)]
        _anonymous_ = ("e", "c")
        _fields_ = [("e", E), ("c", C)]
    _fields_ = [("dwDebugEventCode", wintypes.DWORD), ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD), ("u", U)]


def run(exe):
    si = ctypes.create_string_buffer(104)
    ctypes.memset(si, 0, 104)
    ctypes.cast(si, ctypes.POINTER(wintypes.DWORD))[0] = 68
    pi = ctypes.create_string_buffer(24)
    cmd = ctypes.create_unicode_buffer('"%s"' % exe)
    ok = k.CreateProcessW(None, cmd, None, None, False, 0x1, None, None, si, pi)  # DEBUG_PROCESS
    if not ok:
        print("CreateProcess FAILED err=%d" % k.GetLastError())
        return None
    base = None
    hproc = ctypes.cast(pi, ctypes.POINTER(wintypes.HANDLE))[0]
    hthread = ctypes.cast(pi, ctypes.POINTER(wintypes.HANDLE))[1]
    ev = DEBUG_EVENT()
    while True:
        if not k.WaitForDebugEvent(ctypes.byref(ev), 5000):
            print("WaitForDebugEvent timeout")
            break
        code = ev.dwDebugEventCode
        if code == CREATE_PROCESS_DEBUG_EVENT:
            base = ev.u.c.lpBaseOfImage
        elif code == EXCEPTION_DEBUG_EVENT:
            rec = ev.u.e.ExceptionRecord
            if rec.ExceptionCode == 0xC0000005:
                addr = rec.ExceptionAddress
                info = list(rec.ExceptionInformation[:2])
                rva = addr - base if base and addr >= base and addr < base + 0x40000 else None
                print("AV! tid=%d addr=0x%x (RVA %s) access=%s target=0x%x" % (
                    ev.dwThreadId, addr,
                    hex(rva) if rva is not None else "external",
                    "read" if info[0] == 0 else "write", info[1]))
                # 模块名 + 该线程寄存器
                mod = wintypes.HANDLE()
                GMHEX = 0x4 | 0x1  # FROM_ADDRESS | UNCHANGED_REFCOUNT
                ctypes.windll.kernel32.GetModuleHandleExW.restype = wintypes.BOOL
                if ctypes.windll.kernel32.GetModuleHandleExW(
                        GMHEX, ctypes.c_wchar_p(None), ctypes.byref(mod)):
                    pass
                # 用 CreateToolhelp32Snapshot 查模块（正确的 MODULEENTRY32 结构）
                class MODULEENTRY32(ctypes.Structure):
                    _fields_ = [("dwSize", wintypes.DWORD), ("th32ModuleID", wintypes.DWORD),
                                ("th32ProcessID", wintypes.DWORD), ("GlblcntUsage", wintypes.DWORD),
                                ("ProccntUsage", wintypes.DWORD), ("modBaseAddress", ctypes.c_void_p),
                                ("modBaseSize", wintypes.DWORD), ("hModule", wintypes.HMODULE),
                                ("szModule", ctypes.c_char * 256), ("szExePath", ctypes.c_char * 260)]
                try:
                    snap = k.CreateToolhelp32Snapshot(0x8, ev.dwProcessId)
                    me = MODULEENTRY32()
                    me.dwSize = ctypes.sizeof(MODULEENTRY32)
                    mods = []
                    if k.Module32First(snap, ctypes.byref(me)):
                        while True:
                            mods.append((me.szModule.decode(errors="replace"),
                                         me.modBaseAddress or 0, me.modBaseSize))
                            if not k.Module32Next(snap, ctypes.byref(me)):
                                break
                    k.CloseHandle(snap)
                    hit = None
                    for nm, mb, ms in mods:
                        if mb <= addr < mb + ms:
                            hit = (nm, mb)
                            break
                    if hit:
                        print("  module: %s+0x%x" % (hit[0], addr - hit[1]))
                    else:
                        print("  module not found")
                    print("  all modules (%d):" % len(mods))
                    for nm, mb, ms in mods:
                        print("    0x%012x %8dKB  %s" % (mb, ms // 1024, nm))
                except Exception as ex:
                    print("  module lookup failed:", ex)
                # 寄存器
                class CONTEXT64(ctypes.Structure):
                    _fields_ = [("P1Home", ctypes.c_uint64), ("P2Home", ctypes.c_uint64),
                                ("P3Home", ctypes.c_uint64), ("P4Home", ctypes.c_uint64),
                                ("P5Home", ctypes.c_uint64), ("P6Home", ctypes.c_uint64),
                                ("ContextFlags", wintypes.DWORD), ("MxCsr", wintypes.DWORD),
                                ("SegCs", wintypes.WORD), ("SegDs", wintypes.WORD),
                                ("SegEs", wintypes.WORD), ("SegFs", wintypes.WORD),
                                ("SegGs", wintypes.WORD), ("SegSs", wintypes.WORD),
                                ("EFlags", wintypes.DWORD),
                                ("Dr0", ctypes.c_uint64), ("Dr1", ctypes.c_uint64),
                                ("Dr2", ctypes.c_uint64), ("Dr3", ctypes.c_uint64),
                                ("Dr6", ctypes.c_uint64), ("Dr7", ctypes.c_uint64),
                                ("Rax", ctypes.c_uint64), ("Rcx", ctypes.c_uint64),
                                ("Rdx", ctypes.c_uint64), ("Rbx", ctypes.c_uint64),
                                ("Rsp", ctypes.c_uint64), ("Rbp", ctypes.c_uint64),
                                ("Rsi", ctypes.c_uint64), ("Rdi", ctypes.c_uint64),
                                ("R8", ctypes.c_uint64), ("R9", ctypes.c_uint64),
                                ("R10", ctypes.c_uint64), ("R11", ctypes.c_uint64),
                                ("R12", ctypes.c_uint64), ("R13", ctypes.c_uint64),
                                ("R14", ctypes.c_uint64), ("R15", ctypes.c_uint64),
                                ("Rip", ctypes.c_uint64)]
                # CONTEXT 结构需要 16 字节对齐
                buf = ctypes.create_string_buffer(ctypes.sizeof(CONTEXT64) + 16)
                ctx = CONTEXT64.from_buffer(buf, 16)
                ctx.ContextFlags = 0x100003  # CONTEXT_FULL_AMD64
                # 打开线程
                k.OpenThread.restype = wintypes.HANDLE
                ht = k.OpenThread(0x1FFFFF, False, ev.dwThreadId)  # THREAD_ALL_ACCESS
                if ht:
                    k.GetThreadContext.restype = wintypes.BOOL
                    if k.GetThreadContext(ht, ctypes.byref(ctx)):
                        print("  RIP=0x%x RSP=0x%x RCX=0x%x RDX=0x%x RAX=0x%x RBX=0x%x" % (
                            ctx.Rip, ctx.Rsp, ctx.Rcx, ctx.Rdx, ctx.Rax, ctx.Rbx))
                        k.ReadProcessMemory.restype = wintypes.BOOL
                        v = ctypes.c_uint64()
                        if k.ReadProcessMemory(hproc, ctypes.c_void_p(ctx.Rsp), ctypes.byref(v), 8, None):
                            print("  [RSP]=0x%x" % v.value)
                        # RIP 处指令字节（16B）
                        ib = ctypes.create_string_buffer(16)
                        if k.ReadProcessMemory(hproc, ctypes.c_void_p(ctx.Rip), ib, 16, None):
                            print("  [RIP] bytes: " + ib.raw[:16].hex())
                    k.CloseHandle(ht)
                k.TerminateProcess(hproc, 1)
                k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
                break
            k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_EXCEPTION_NOT_HANDLED)
            continue
        elif code == EXIT_PROCESS_DEBUG_EVENT:
            print("clean exit (no AV)")
            break
        k.ContinueDebugEvent(ev.dwProcessId, ev.dwThreadId, DBG_CONTINUE)
    k.CloseHandle(hproc)
    k.CloseHandle(hthread)
    return base


if __name__ == "__main__":
    exe = sys.argv[1]
    n = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    for i in range(n):
        print("run %d:" % (i + 1))
        run(exe)
