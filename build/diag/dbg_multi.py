"""多断点执行流追踪：在多个 RVA 插 int3，记录命中序列 + 寄存器，定位失控点。

用法: python build/dbg_multi.py <exe> <rva> [rva...]
"""
import struct
import sys
from ctypes import wintypes
import ctypes as C

k32 = C.WinDLL("kernel32", use_last_error=True)

CREATE_PROCESS_DEBUG_EVENT = 3
EXIT_PROCESS_DEBUG_EVENT = 5
EXCEPTION_DEBUG_EVENT = 1
EXCEPTION_BREAKPOINT = 0x80000003
EXCEPTION_SINGLE_STEP = 0x80000004
DBG_CONTINUE = 0x00010002
DBG_EXCEPTION_NOT_HANDLED = 0x80010001


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


IMAGE_BASE = 0x140000000


def main():
    exe = sys.argv[1]
    rvas = [int(a, 16) for a in sys.argv[2:]]
    si = STARTUPINFO()
    si.cb = C.sizeof(si)
    pi = PROCESS_INFORMATION()
    ok = k32.CreateProcessW(exe, None, None, None, False,
                            0x00000004 | 0x00000002,  # SUSPENDED | DEBUG_PROCESS
                            None, None, C.byref(si), C.byref(pi))
    if not ok:
        print("CreateProcess 失败", C.get_last_error())
        return 1
    hp, ht = pi.hProcess, pi.hThread
    k32.DebugSetProcessKillOnExit(False)

    # 写 int3
    orig = {}
    for rva in rvas:
        addr = IMAGE_BASE + rva
        buf = C.c_char(1)
        k32.ReadProcessMemory(hp, C.c_void_p(addr), C.byref(buf), 1, None)
        orig[rva] = buf.value
        k32.WriteProcessMemory(hp, C.c_void_p(addr), C.c_char(b"\xcc"), 1, None)
    print(f"断点: {[hex(r) for r in rvas]}")

    # 继续主线程（loader 断点会先命中）
    n = 0
    def cont():
        return k32.ContinueDebugEvent(de.dwProcessId, de.dwThreadId, DBG_CONTINUE)

    while True:
        if not k32.WaitForDebugEvent(C.byref(de), 15000):
            print("超时，无事件")
            break
        code = de.dwEventCode() if callable(getattr(de, "dwEventCode", None)) else de.dwEventCode
        code = de.dwEventCode
        if code == EXCEPTION_DEBUG_EVENT:
            info = C.cast(C.byref(de.u), C.POINTER(EXCEPTION_DEBUG_INFO)).contents
            er = info.ExceptionRecord
            addr = er.ExceptionAddress or 0
            if er.ExceptionCode == EXCEPTION_BREAKPOINT:
                if addr == 0:  # 初始 loader 断点
                    cont()
                    # 恢复主线程
                    k32.ResumeThread(ht)
                    continue
                rva = addr - IMAGE_BASE
                ctx = C.c_byte * 1232
                c = ctx()
                k32.GetThreadContext(ht, C.byref(c))  # 未必是本线程，仅尽力
                if rva in orig:
                    # 还原指令
                    k32.WriteProcessMemory(hp, C.c_void_p(addr), C.c_char(orig[rva]), 1, None)
                    print(f"命中#{n} RVA 0x{rva:X}")
                    n += 1
                    if n >= 40:
                        print("命中过多，终止")
                        k32.TerminateProcess(hp, 1)
                        break
                    # 单步后重设
                    k32.FlushInstructionCache(hp, C.c_void_p(addr), 1)
                cont()
                continue
            if er.ExceptionCode == EXCEPTION_SINGLE_STEP:
                cont()
                continue
            # 真异常
            print(f"异常 0x{er.ExceptionCode:X} @RVA 0x{addr - IMAGE_BASE:X}")
            print(f"  参数: {[er.ExceptionInformation[i] for i in range(min(er.NumberParameters,2))]}")
            k32.TerminateProcess(hp, 1)
            break
        if code == EXIT_PROCESS_DEBUG_EVENT:
            print("进程退出")
            break
        cont()
    k32.CloseHandle(hp)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
