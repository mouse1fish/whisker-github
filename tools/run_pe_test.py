"""Run a PE exe via CreateProcessW with stdout/stderr pipe capture.

Usage: python tools/run_pe_test.py <exe> [timeout_ms]
Returns: prints stdout (repr) and exit code. Exit code of this script:
0 = exe ran and exited 0; 1 = launch failed; 2 = nonzero/timeout exit.
"""
import sys, ctypes
from ctypes import wintypes

k = ctypes.windll.kernel32
k.CreateProcessW.restype = wintypes.BOOL


class SECURITY_ATTRIBUTES(ctypes.Structure):
    _fields_ = [("nLength", wintypes.DWORD),
                ("lpSecurityDescriptor", ctypes.c_void_p),
                ("bInheritHandle", wintypes.BOOL)]


class STARTUPINFO(ctypes.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", ctypes.c_wchar_p),
                ("lpDesktop", ctypes.c_wchar_p), ("lpTitle", ctypes.c_wchar_p),
                ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


def run(exe, timeout_ms=10000):
    sa = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, True)
    r, w = wintypes.HANDLE(), wintypes.HANDLE()
    if not k.CreatePipe(ctypes.byref(r), ctypes.byref(w), ctypes.byref(sa), 0):
        print("pipe fail err=%d" % k.GetLastError())
        return 1
    k.SetHandleInformation(r, 1, 0)
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    si.dwFlags = 0x100  # STARTF_USESTDHANDLES
    si.hStdInput = None
    si.hStdOutput = w
    si.hStdError = w
    pi = PROCESS_INFORMATION()
    cmd = ctypes.create_unicode_buffer('"%s"' % exe)
    ok = k.CreateProcessW(None, cmd, None, None, True, 0, None, None,
                          ctypes.byref(si), ctypes.byref(pi))
    if not ok:
        print("CreateProcess FAILED err=%d" % k.GetLastError())
        k.CloseHandle(r)
        return 1
    k.CloseHandle(w)
    out = b""
    buf = ctypes.create_string_buffer(8192)
    n = wintypes.DWORD()
    while k.ReadFile(r, buf, 8192, ctypes.byref(n), None) and n.value > 0:
        out += buf.raw[:n.value]
    wait = k.WaitForSingleObject(pi.hProcess, timeout_ms)
    code = wintypes.DWORD()
    k.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
    k.CloseHandle(pi.hProcess)
    k.CloseHandle(pi.hThread)
    k.CloseHandle(r)
    print("stdout = %r" % out)
    print("exit = 0x%x (%s)" % (code.value, "TIMEOUT" if wait else "OK"))
    if wait:
        return 2
    return 0 if code.value == 0 else 2


if __name__ == "__main__":
    exe = sys.argv[1]
    tmo = int(sys.argv[2]) if len(sys.argv) > 2 else 10000
    sys.exit(run(exe, tmo))
