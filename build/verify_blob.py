d = open(r"G:/trea-Eon-os/eonos/native/httpd.exe","rb").read()
# .text 从 RVA 0x1000 / 文件 0x200 起；blob 从段首开始；rt_init 在 blob+44（RVA 0x102C）
off = 0x200 + 0x2C
print("httpd.exe blob+44 (rt_init 首 16 字节):", d[off:off+16].hex(" "))
print("预期（push rbp; mov rbp,rsp; and rsp,-16; sub...）: 55 48 89 e5 48 83 e4 f0 ...")
# 对比工程根的 rt_blob.bin
blob = open(r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/build/rt_blob.bin","rb").read()
print("rt_blob.bin blob+44:", blob[44:44+16].hex(" "))
print("一致:", d[off:off+16] == blob[44:60])
