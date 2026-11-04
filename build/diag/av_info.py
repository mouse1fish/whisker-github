"""最小 AV 现场：打印异常地址（ExceptionInformation[1]）与访问类型。

用法: python build/av_info.py <exe>
"""
import ctypes as C
from ctypes import wintypes

k32 = C.WinDLL("kernel32", use_last_error=True)
IMAGE_BASE = 0x140000000


class STARTUPINFO(C.Structure):
    _fields_ = [("cb", wintypes.DWORD), ("lpReserved", wintypes.LPSTR),
                ("lpDesktop", wintypes.LPSTR), ("lpTitle", wintypes.LPSTR),
                ("dwX", wintypes.DWORD), ("dwY", wintypes.DWORD),
                ("dwXSize", wintypes.DWORD), ("dwYSize", wintypes.DWORD),
                ("dwXCountChars", wintypes.DWORD), ("dwYCountChars", wintypes.DWORD),
                ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", C.c_void_p), ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class PROCESS_INFORMATION(C.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


class EXCEPTION_RECORD(C.Structure):
    _fields_ = [("ExceptionCode", wintypes.DWORD), ("ExceptionFlags", wintypes.DWORD),
                ("ExceptionRecord", C.c_void_p), ("ExceptionAddress", C.c_void_p),
                ("NumberParameters", wintypes.DWORD),
                ("ExceptionInformation", C.c_void_p * 15)]


class EXCEPTION_DEBUG_INFO(C.Structure):
    _fields_ = [("ExceptionRecord", EXCEPTION_RECORD), ("dwFirstChance", wintypes.DWORD)]


class DEBUG_EVENT(C.Structure):
    _fields_ = [("dwDebugEventCode", wintypes.DWORD), ("dwProcessId", wintypes.DWORD),
                ("dwThreadId", wintypes.DWORD), ("u", C.c_byte * 160)]


class CONTEXT_AMD64(C.Structure):
    _fields_ = [("Pad", C.c_byte * 1232)]


def main():
    import sys
    exe = sys.argv[1]
    si = STARTUPINFO(); si.cb = C.sizeof(si)
    pi = PROCESS_INFORMATION()
    if not k32.CreateProcessW(exe, None, None, None, False, 0x00000002,
                              None, None, C.byref(si), C.byref(pi)):
        print("创建失败", C.get_last_error()); return 1
    hp, ht = pi.hProcess, pi.hThread
    de = DEBUG_EVENT()
    for _ in range(200):
        if not k32.WaitForDebugEvent(C.byref(de), 8000):
            print("超时"); break
        code = de.dwDebugEventCode
        if code == 1:  # EXCEPTION
            info = C.cast(C.byref(de.u), C.POINTER(EXCEPTION_DEBUG_INFO)).contents
            er = info.ExceptionRecord
            if er.ExceptionCode == 0x80000003 and not er.ExceptionAddress:
                k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, 0x00010002)
                k32.ResumeThread(ht)
                continue
            if er.ExceptionCode == 0x80000003:
                k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, 0x00010002)
                continue
            if er.ExceptionCode == 0x80000004:
                k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, 0x00010002)
                continue
            addr = er.ExceptionAddress or 0
            p = int(er.NumberParameters)
            raw = [er.ExceptionInformation[i] for i in range(15)]
            args = [0 if v is None else v for v in raw[:max(p, 2)]]
            print(f"异常 0x{er.ExceptionCode:X} @RVA 0x{addr - IMAGE_BASE:X}  NumberParameters={p}")
            print(f"  原始参数: {[hex(v) if v else '0' for v in raw[:max(p,2)]]}")
            if args:
                kind = {0: "读", 1: "写", 8: "执行"}.get(args[0], f"类型{args[0]}")
                print(f"  类型={kind} 目标地址=0x{args[1]:X}" if len(args) >= 2 else f"  类型={kind}")
            k32.TerminateProcess(hp, 1)
            break
        if code == 5:  # EXIT_PROCESS
            print("进程退出")
            break
        k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, 0x00010002)
    k32.CloseHandle(hp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
