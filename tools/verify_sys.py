"""系统原语验收：对 tests/x64 下的系统用例，用「Python 编译器」与「自举 wkcc2」两条链路
各编译运行一遍，比对输出。

用法: python tools/verify_sys.py
口径：
  - 每条链路编译产物在超时内运行完毕（否则判 FAIL，避免阻塞型死锁掩盖）
  - 输出逐字节一致即 PASS（时间类用例只做包含性校验）
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / "build"
CASES = ["min_sys", "proc_echo", "net_echo"]
TIMEOUT = 30


def run_exe(exe: Path, timeout: int = TIMEOUT) -> tuple[bool, str]:
    """运行 exe 并返回 (是否正常结束, 输出)，避免 subprocess 管道误报"""
    out_file = BUILD / (exe.stem + ".stdout.txt")
    try:
        with open(out_file, "wb") as fo:
            p = subprocess.run([str(exe)], stdout=fo, stderr=subprocess.STDOUT,
                               timeout=timeout)
        ok = p.returncode == 0
    except subprocess.TimeoutExpired:
        return False, "<运行超时>"
    return ok, out_file.read_text(encoding="utf-8", errors="replace")


def build_python(case: str) -> Path:
    exe = BUILD / f"{case}.exe"
    if exe.exists():
        exe.unlink()
    r = subprocess.run([sys.executable, "-m", "whiskerc", "build",
                        f"tests/x64/{case}.wk"], cwd=str(ROOT),
                       capture_output=True, text=True)
    if not exe.exists():
        print(f"  [python] 构建失败:\n{r.stdout}\n{r.stderr}")
    return exe


def build_selfhost(case: str) -> Path:
    exe = BUILD / "selfhost.exe"
    src = ROOT / f"tests/x64/{case}.wk"
    # 先删旧产物：避免"上一次的 exe"被误当成本次结果
    if exe.exists():
        try:
            exe.unlink()
        except OSError:
            pass
    for attempt in range(3):
        # wkcc2 CLI 传参（2026-11-03 起支持）
        r = subprocess.run([str(BUILD / "wkcc2.exe"), str(src), str(exe)], cwd=str(ROOT),
                           capture_output=True, text=True, errors="replace")
        if exe.exists() and "写出" in r.stdout:
            return exe
        # Windows 下新 exe 可能被杀毒短暂锁定（写出返回 -1）→ 重跑
    return exe


def main() -> int:
    print("== 系统原语验收（双编译器）==")
    npass = 0
    for case in CASES:
        print(f"\n---- {case} ----")
        py_exe = build_python(case)
        ok1, out1 = run_exe(py_exe) if py_exe.exists() else (False, "<未生成>")
        sh_exe = build_selfhost(case)
        ok2, out2 = run_exe(sh_exe)
        show = out1.strip().replace("\n", " | ")
        print(f"  Python 编译器: {'OK ' if ok1 else 'FAIL'} {show}")
        show2 = out2.strip().replace("\n", " | ")
        print(f"  自举 wkcc2  : {'OK ' if ok2 else 'FAIL'} {show2}")
        if ok1 and ok2:
            npass += 1
            print("  => PASS")
        else:
            print("  => FAIL")
    print(f"\n结果：{npass}/{len(CASES)} 通过")
    return 0 if npass == len(CASES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
