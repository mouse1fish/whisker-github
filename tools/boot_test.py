# -*- coding: utf-8 -*-
"""自举链测试：wkcc.exe 编译 lex_input.txt → selfhost.exe → CreateProcessW 运行。"""
import ctypes, sys
from ctypes import wintypes

k = ctypes.windll.kernel32


def run(path, timeout=15000):
    k.CreateProcessW.restype = wintypes.BOOL
    si = ctypes.create_string_buffer(104)
    ctypes.memset(si, 0, 104)
    ctypes.cast(si, ctypes.POINTER(wintypes.DWORD))[0] = 104
    pi = ctypes.create_string_buffer(24)
    if not k.CreateProcessW(path, None, None, None, False, 0, None, None, si, pi):
        return ("CREATE_FAIL", k.GetLastError())
    h = ctypes.cast(pi, ctypes.POINTER(wintypes.HANDLE))[1]
    k.WaitForSingleObject(h, timeout)
    code = wintypes.DWORD()
    k.GetExitCodeProcess(h, ctypes.byref(code))
    k.CloseHandle(h)
    return code.value


if __name__ == "__main__":
    r1 = run(r"H:\trea-xiancheng-bianyiqi\build\wkcc.exe")
    print(f"wkcc.exe: exit={r1}")
    r2 = run(r"H:\trea-xiancheng-bianyiqi\build\selfhost.exe")
    print(f"selfhost.exe: exit={r2}")
