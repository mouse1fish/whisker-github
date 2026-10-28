# -*- coding: utf-8 -*-
"""CreateProcessW 版验收脚本。

与 verify.py 相同的用例表，但改用 Win32 CreateProcessW + 匿名管道启动 exe。
bash/cmd/subprocess 对手工构建 PE 的启动结果不可靠（交接文档结论），
本脚本是退出码与 stdout 的唯一可信来源。

用法（项目根目录）：  python tools/verify_cp.py [单个用例名 ...]
"""
from __future__ import annotations

import ctypes
import sys
from ctypes import wintypes
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tools.verify import GOOD, BAD  # noqa: E402
from whiskerc.cli import front_end  # noqa: E402
from whiskerc.codegen_x64 import X64Program  # noqa: E402

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
                ("dwFillAttribute", wintypes.DWORD), ("dwFlags", wintypes.WORD),
                ("wShowWindow", wintypes.WORD), ("cbReserved2", wintypes.WORD),
                ("lpReserved2", ctypes.c_void_p), ("hStdInput", wintypes.HANDLE),
                ("hStdOutput", wintypes.HANDLE), ("hStdError", wintypes.HANDLE)]


class PROCESS_INFORMATION(ctypes.Structure):
    _fields_ = [("hProcess", wintypes.HANDLE), ("hThread", wintypes.HANDLE),
                ("dwProcessId", wintypes.DWORD), ("dwThreadId", wintypes.DWORD)]


def run_exe(exe: Path, timeout_ms: int = 60000) -> tuple[int, str]:
    """CreateProcessW 直测：返回 (退出码, stdout+stderr 文本)。"""
    sa = SECURITY_ATTRIBUTES(ctypes.sizeof(SECURITY_ATTRIBUTES), None, True)
    r, w = wintypes.HANDLE(), wintypes.HANDLE()
    if not k.CreatePipe(ctypes.byref(r), ctypes.byref(w), ctypes.byref(sa), 0):
        return -1, f"CreatePipe 失败 err={k.GetLastError()}"
    k.SetHandleInformation(r, 1, 0)  # 句柄不可继承
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
        k.CloseHandle(r)
        k.CloseHandle(w)
        return -1, f"CreateProcess 失败 err={k.GetLastError()}"
    k.CloseHandle(w)
    out = b""
    buf = ctypes.create_string_buffer(65536)
    n = wintypes.DWORD()
    # 读到 EOF（子进程退出时写端关闭）
    while k.ReadFile(r, buf, 65536, ctypes.byref(n), None) and n.value > 0:
        out += buf.raw[:n.value]
    wait = k.WaitForSingleObject(pi.hProcess, timeout_ms)
    if wait:  # 超时兜底
        k.TerminateProcess(pi.hProcess, 0xFFFFFFFF)
    code = wintypes.DWORD()
    k.GetExitCodeProcess(pi.hProcess, ctypes.byref(code))
    k.CloseHandle(pi.hProcess)
    k.CloseHandle(pi.hThread)
    k.CloseHandle(r)
    rc = 0xFFFFFFFE if wait else code.value
    return rc, out.decode("utf-8", errors="replace")


def build_x64(program, name: str) -> Path:
    xp = X64Program(program)
    xp.emit()
    data = xp.pe.build(xp.a, xp.a.labels["whisker_entry"])
    out = ROOT / "build" / f"{name}.exe"
    out.write_bytes(data)
    return out


def main() -> int:
    only = set(sys.argv[1:])
    results: list[bool] = []

    for src, expect in GOOD:
        if only and not any(o in src for o in only):
            continue
        path = ROOT / src
        program, diag = front_end(path)
        if not diag.ok():
            print(f"[FAIL] {src} 前端报错\n{diag.render(str(path))}")
            results.append(False)
            continue
        exe = build_x64(program, path.stem)
        rc, text = run_exe(exe)
        ok = rc == 0 and all(e in text for e in expect)
        print(f"[{'PASS' if ok else 'FAIL'}] {src}（退出码 {rc}）")
        if not ok:
            print("---- 实际输出 ----\n" + text)
        results.append(ok)

    for src, expect_msg in BAD:
        if only and not any(o in src for o in only):
            continue
        path = ROOT / src
        _p, diag = front_end(path)
        msgs = "\n".join(m for _k, _l, _c, m in diag.items)
        ok = (not diag.ok()) and (expect_msg in msgs)
        print(f"[{'PASS' if ok else 'FAIL'}] {src} 编译期被拦下：{expect_msg}")
        results.append(ok)

    print("")
    print(f"==== 验收结果（CreateProcessW）：{sum(results)}/{len(results)} 通过 ====")
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
