"""自研 PE/x64 后端排查脚本：逐级验证容器 → 运行时 → 完整程序"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from whiskerc.asm_x64 import RCX, Asm          # noqa: E402
from whiskerc.pe_x64 import PEBuilder          # noqa: E402
from whiskerc.runtime_x64 import emit_runtime  # noqa: E402

OUT = ROOT / "build"


def run(name: str, data: bytes) -> int:
    OUT.mkdir(exist_ok=True)
    exe = OUT / name
    exe.write_bytes(data)
    rc = subprocess.call([str(exe)])
    print(f"  {name}: 退出码 {rc} (0x{rc & 0xFFFFFFFF:08X})")
    return rc


def variant_ret() -> bytes:
    """入口只调 ExitProcess —— 验证 PE 容器合法"""
    a = Asm()
    pe = PEBuilder()
    pe.declare_imports(["ExitProcess"])
    a.label("whisker_entry")
    a.mov_ri(RCX, 0)
    a.call_rip("imp_ExitProcess")
    return pe.build(a, a.labels["whisker_entry"])


def variant_init_only() -> bytes:
    """入口调用 rt_init（内部调 kernel32：GetStdHandle / QPC / VirtualAlloc）后退出"""
    a = Asm()
    pe = PEBuilder()
    emit_runtime(a, pe)
    pe.declare_imports(["ExitProcess"])
    a.label("whisker_entry")
    a.call("rt_init")
    a.mov_ri(RCX, 0)
    a.call_rip("imp_ExitProcess")
    return pe.build(a, a.labels["whisker_entry"])


def variant_print() -> bytes:
    """入口调用 rt_init + 打印一行固定字符串"""
    a = Asm()
    pe = PEBuilder()
    emit_runtime(a, pe)
    pe.declare_imports(["ExitProcess"])
    pe.rdata_item("demo_str", "自研后端打印成功\n".encode("utf-8") + b"\x00")
    a.label("whisker_entry")
    a.call("rt_init")
    a.lea_rip(RCX, "demo_str")
    a.call("rt_print_cstr")
    a.call("rt_print_end")
    a.mov_ri(RCX, 0)
    a.call_rip("imp_ExitProcess")
    return pe.build(a, a.labels["whisker_entry"])


def variant_int() -> bytes:
    """打印整数与布尔，验证进制转换与字节写"""
    a = Asm()
    pe = PEBuilder()
    emit_runtime(a, pe)
    pe.declare_imports(["ExitProcess"])
    a.label("whisker_entry")
    a.call("rt_init")
    a.call("rt_print_begin")
    a.mov_ri(RCX, -1234567)
    a.call("rt_print_int")
    a.mov_ri(RCX, 1)
    a.call("rt_print_bool")
    a.call("rt_print_end")
    a.mov_ri(RCX, 0)
    a.call_rip("imp_ExitProcess")
    return pe.build(a, a.labels["whisker_entry"])


if __name__ == "__main__":
    print("=== 1) 入口只调 ExitProcess ===")
    run("dbg_ret.exe", variant_ret())
    print("=== 2) 入口调 rt_init ===")
    run("dbg_init.exe", variant_init_only())
    print("=== 3) rt_init + 打印字符串 ===")
    run("dbg_print.exe", variant_print())
    print("=== 4) 打印整数/布尔 ===")
    run("dbg_int.exe", variant_int())