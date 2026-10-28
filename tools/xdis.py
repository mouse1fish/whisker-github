# -*- coding: utf-8 -*-
"""反汇编 wkcc2/selfhost 用户代码段。

用法:
  python tools/dis.py <exe> <rva_hex> [len_hex]   # 反汇编 rva 起 len 字节（默认 0x60）
"""
import struct, sys
import capstone

def load(exe):
    data = open(exe, 'rb').read()
    pe = struct.unpack_from('<I', data, 0x3C)[0]
    nsec = struct.unpack_from('<H', data, pe + 6)[0]
    opt = struct.unpack_from('<H', data, pe + 20)[0]
    secs = []
    for i in range(nsec):
        o = pe + 24 + opt + i * 40
        name = data[o:o + 8].rstrip(b'\x00').decode()
        vsize, vaddr, rsize, raddr = struct.unpack_from('<IIII', data, o + 8)
        secs.append((name, vaddr, vsize, raddr, rsize))
    return data, secs

def rd(data, secs, rva, n):
    for name, va, vs, ra, rs in secs:
        if va <= rva < va + max(vs, rs):
            off = ra + (rva - va)
            return data[off:off + n]
    return b''

def main():
    exe = sys.argv[1]
    rva = int(sys.argv[2], 16)
    n = int(sys.argv[3], 16) if len(sys.argv) > 3 else 0x60
    data, secs = load(exe)
    md = capstone.Cs(capstone.CS_ARCH_X86, capstone.CS_MODE_64)
    code = rd(data, secs, rva, n)
    for i in md.disasm(code, 0x140000000 + rva):
        ann = ''
        if i.mnemonic in ('call', 'jmp') and i.op_str.startswith('0x'):
            t = int(i.op_str, 16) - 0x140000000
            ann = '  ; ->0x%x' % t
        print('%05x: %-24s %s %s%s' % (
            i.address - 0x140000000,
            ' '.join('%02x' % b for b in i.bytes),
            i.mnemonic, i.op_str, ann))

if __name__ == '__main__':
    main()
