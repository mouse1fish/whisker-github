p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
# 1) 字段
old = '''    outPath: Str = "build/selfhost.exe"     # 输出 exe（同上）'''
new = '''    outPath: Str = "build/selfhost.exe"     # 输出 exe（同上）
    blobPath: Str = "build/rt_blob.bin"     # 运行时 blob（第 3 个参数可覆盖；SDK 用）'''
assert old in s, "字段"; s = s.replace(old, new)
# 2) parseCli 第三个参数
old = '''            a2: Str = nextArg()
            if strLen(a2) > 0 {
                outPath = a2
            }
        }'''
new = '''            a2: Str = nextArg()
            if strLen(a2) > 0 {
                outPath = a2
            }
            a3: Str = nextArg()
            if strLen(a3) > 0 {
                blobPath = a3
            }
        }'''
assert old in s, "parseCli"; s = s.replace(old, new)
# 3) 两处 readBytes blob 用 blobPath
c = s.count('readBytes("build/rt_blob.bin", blob, RT_DATA_OFF + RT_DATA_LEN)')
assert c == 2, f"blob readBytes 出现 {c} 次"
s = s.replace('readBytes("build/rt_blob.bin", blob, RT_DATA_OFF + RT_DATA_LEN)',
              'readBytes(blobPath, blob, RT_DATA_OFF + RT_DATA_LEN)')
open(p, "w", encoding="utf-8").write(s)
print("blob 路径参数化 OK")
