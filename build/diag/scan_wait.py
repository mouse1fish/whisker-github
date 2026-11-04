import struct
blob = open(r"build/rt_blob.bin","rb").read()
# rt_proc_wait @0x11EE（新偏移 4590=0x11EE），rt_proc_free @4675=0x1243
IAT_RVA = 218424
start, end = 4590, 4675
for i in range(start, end):
    if blob[i] == 0xFF and blob[i+1] == 0x15:
        rel = struct.unpack_from("<i", blob, i+2)[0]
        slot_rva = IAT_RVA + (i + 6 + rel) - 0x1000  # 目标 = IAT 槽的 RVA（blob 用固定 RVA）
        # 实际：目标地址 = i+6+rel（blob 内 text 偏移 + 0x1000 = RVA）
        tgt_rva = 0x1000 + i + 6 + rel
        idx = (tgt_rva - IAT_RVA) // 8
        print(f"rt_proc_wait+{i-start}: call [IAT slot {idx}] (blob off 0x{i:X})")
