#!/usr/bin/env python3
"""check_strtof.py — wkcc.wk strToFbits 算法的性质对拍测试

把 tools/wkcc.wk 里 strToFbits 的算法逐行复刻为 Python，
对固定边界样本 + 随机样本，比对算法输出的 IEEE 754 位模式
与 Python float()（strtod 正确舍入）的位模式。

覆盖范围：≤17 位小数（Int64 安全域）；超出部分两侧一致地截断。
验收标准：0 例不一致。

用法（项目根目录）: python tools/check_strtof.py [样本数]
"""
import random
import struct
import sys


def str_to_fbits(text: str) -> int:
    """wkcc.wk strToFbits 的逐行复刻（语义同 Whisker 版，/ 与 % 均为向零截断）"""
    n = len(text)
    i_part = 0
    n_part = 0
    k = 0
    seen_dot = 0
    j = 0
    while j < n:
        c = ord(text[j])
        if c == 46:
            seen_dot = 1
        else:
            if seen_dot == 0:
                i_part = i_part * 10 + c - 48
            elif k < 17:
                n_part = n_part * 10 + c - 48
                k = k + 1
        j = j + 1
    d = 1
    t2 = 0
    while t2 < k:
        d = d * 10
        t2 = t2 + 1
    n_val = i_part * d + n_part
    if n_val == 0:
        return 0
    q = n_val // d
    e = 0
    bits54 = 0
    cnt = 0
    rem = 0
    t3 = -1
    p2j = 0
    if q == 0:
        while n_val < d:
            n_val = n_val * 2
            e = e - 1
        bits54 = 1
        cnt = 1
        rem = n_val - d
    elif q == 1:
        e = 0
        bits54 = 1
        cnt = 1
        rem = n_val - d
    else:
        p2 = q
        while p2 > 0:
            p2 = p2 // 2
            e = e + 1
        e = e - 1
        p2j = 1
        t3 = 0
        while t3 < e:
            p2j = p2j * 2
            t3 = t3 + 1
        rem = n_val - q * d
    if q >= 2:
        while t3 >= 0:
            if cnt == 54:
                break
            if (q // p2j) % 2 == 1:
                bits54 = bits54 * 2 + 1
            else:
                bits54 = bits54 * 2
            cnt = cnt + 1
            p2j = p2j // 2
            t3 = t3 - 1
    while cnt < 54:
        rem = rem * 2
        if rem >= d:
            bits54 = bits54 * 2 + 1
            rem = rem - d
        else:
            bits54 = bits54 * 2
        cnt = cnt + 1
    sticky = 0
    if rem > 0:
        sticky = 1
    if t3 >= 0:
        if (q % (p2j * 2)) > 0:
            sticky = 1
    round_b = bits54 % 2
    mant = bits54 // 2
    if round_b == 1:
        if sticky == 1 or mant % 2 == 1:
            mant = mant + 1
    if mant >= 9007199254740992:      # ≥ 2^53：进位溢出 → 右移 + e+1
        mant = mant // 2
        e = e + 1
    mf = mant - 4503599627370496      # 去隐藏位（2^52）
    ef = e + 1023
    if ef >= 2047:
        return 9218868437227405312    # +inf
    if ef <= 0:
        return 0                      # 次正规简化为 0
    return ef * 4503599627370496 + mf


def expect_bits(text: str) -> int:
    return struct.unpack("<Q", struct.pack("<d", float(text)))[0]


def gen_samples(count: int):
    fixed = [
        "3.14", "0.5", "1.5", "2.25", "0.1", "0.07", "0.2", "0.3",
        "42.0" if False else "42", "7", "0", "0.000001", "999999999",
        "12345.6789", "1.00000000000000001", "0.99999999999999999",
        "3.14159265358979", "2.718281828459045", "100.001", "0.0625",
        "1e2" if False else "123456789.123456789", "5.125", "1.1",
    ]
    for t in fixed:
        yield t
    rng = random.Random(20261106)
    for _ in range(count):
        k = rng.randint(0, 9)
        i_part = rng.randint(0, 10 ** rng.randint(0, 12))
        n_part = rng.randint(0, 10 ** k - 1) if k > 0 else 0
        if k > 0:
            yield f"{i_part}.{n_part:0{k}d}"
        else:
            yield str(i_part)


def main() -> int:
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 2000
    total = 0
    fails = []
    for text in gen_samples(count):
        got = str_to_fbits(text)
        want = expect_bits(text)
        total += 1
        if got != want:
            fails.append((text, got, want))
    for text, got, want in fails[:10]:
        print(f"[FAIL] {text!r}: got {got} (0x{got:016X}) want {want} (0x{want:016X})")
    if fails:
        print(f"==== strToFbits 性质对拍：{total - len(fails)}/{total} 一致，{len(fails)} 例不一致 ====")
        return 1
    print(f"==== strToFbits 性质对拍：{total}/{total} 全部一致（含固定边界 + 随机样本）====")
    return 0


if __name__ == "__main__":
    sys.exit(main())
