"""x64 后端崩溃二分定位：逐个微程序编译运行，看哪一步开始崩"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from whiskerc.cli import front_end                    # noqa: E402
from whiskerc.codegen_x64 import X64Program           # noqa: E402

CASES: list[tuple[str, str]] = [
    ("field_write", """
actor Main {
    var n: Int = 0;
    on Start() { n = 7; }
}
"""),
    ("field_print", """
actor Main {
    var n: Int = 0;
    on Start() { n = 7; print("n=", n); }
}
"""),
    ("send_noparam", """
actor Main {
    on Start() { self.send(Tick()); }
    on Tick() { print("tick"); }
}
"""),
    ("send_withparam", """
actor Main {
    var n: Int = 0;
    on Start() { self.send(Bump(1)); }
    on Bump(step: Int) { n = n + step; print("n=", n); }
}
"""),
    ("send_twoparams", """
actor Main {
    var n: Int = 0;
    on Start() { self.send(Bump(1, 2)); }
    on Bump(a: Int, b: Int) { n = a + b; print("n=", n); }
}
"""),
    ("print_three", """
actor Main {
    on Start() { print("a=", 1, "b=", 2); }
}
"""),
]


def run_case(name: str, src: str) -> int:
    d = ROOT / "build" / "micro"
    d.mkdir(parents=True, exist_ok=True)
    f = d / f"{name}.whisker"
    f.write_text(src, encoding="utf-8")
    program, diag = front_end(f)
    if not diag.ok():
        print(f"[SKIP] {name} 前端报错\n{diag.render(str(f))}")
        return -1
    xp = X64Program(program)
    xp.emit()
    data = xp.pe.build(xp.a, xp.a.labels["whisker_entry"])
    exe = d / f"{name}.exe"
    exe.write_bytes(data)
    rc = subprocess.call([str(exe)])
    flag = "OK  " if rc == 0 else "崩溃"
    print(f"[{flag}] {name}: 退出码 {rc} (0x{rc & 0xFFFFFFFF:08X})")
    return rc


if __name__ == "__main__":
    for n, s in CASES:
        run_case(n, s)