p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
old = '''        # 分配用户代码区（64KB）和 .rdata 区（64KB）
        cbuf = alloc(65536)
        rbuf = alloc(65536)'''
new = '''        # 分配用户代码区（256KB）和 .rdata 区（256KB）
        # 依据：.text 窗口守卫限定 cw<=128KB，exe 总大小 <= ~180KB，256KB 有确定富余
        # （历史教训：64KB 容器在 wkcc 自身体积超过 64KB 后溢出，踩坏紧邻的 rbuf 字符串池）
        cbuf = alloc(262144)
        rbuf = alloc(262144)'''
assert old in s, "缓冲分配"
s = s.replace(old, new)
s = s.replace("    rbuf: Ptr                  # .rdata 区（64KB）", "    rbuf: Ptr                  # .rdata 区（256KB）")
open(p, "w", encoding="utf-8").write(s)
print("缓冲扩容 OK")
