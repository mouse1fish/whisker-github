p = r"tools/verify_sys.py"
s = open(p, encoding="utf-8").read()
old = '''def build_selfhost(case: str) -> Path:
    (BUILD / "lex_input.txt").write_bytes((ROOT / f"tests/x64/{case}.wk").read_bytes())
    exe = BUILD / "selfhost.exe"
    # 先删旧产物：避免"上一次的 exe"被误当成本次结果
    if exe.exists():
        try:
            exe.unlink()
        except OSError:
            pass
    for attempt in range(3):
        r = subprocess.run([str(BUILD / "wkcc2.exe")], cwd=str(ROOT),
                           capture_output=True, text=True, errors="replace")
        if exe.exists() and "写出" in r.stdout:
            return exe
        # Windows 下新 exe 可能被杀毒短暂锁定（写出返回 -1）→ 重跑
    return exe'''
new = '''def build_selfhost(case: str) -> Path:
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
    return exe'''
assert old in s, "verify_sys"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("verify_sys CLI 化 OK")
