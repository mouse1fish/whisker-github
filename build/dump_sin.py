blob = open(r"build/rt_blob.bin","rb").read()
off = 5142   # OFF_SIN16
print("rt_sin16 机器码:", blob[off:off+20].hex(" "))
# rt_cos16 在 5133
print("rt_cos16 机器码:", blob[5133:5133+10].hex(" "))
# g_sin 表：data 段起点 = RT_DATA_OFF=9146；g_sin 的偏移需从 data 布局看——直接找 RT_DATA 里的表
print("blob 长度:", len(blob), " data 起点:", 9146)
