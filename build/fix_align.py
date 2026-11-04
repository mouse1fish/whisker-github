# 1) asm_x64.py：align_rsp 助手
p = r"whiskerc/asm_x64.py"
s = open(p, encoding="utf-8").read()
s = s.replace(
    '''    def movsxd_rax_eax(self) -> None:''',
    '''    def align_rsp(self) -> None:
        """and rsp, -16（48 83 E4 F0）——帧内动态栈对齐，容忍未对齐的调用入口"""
        self.emit(0x48, 0x83, 0xE4, 0xF0)

    def movsxd_rax_eax(self) -> None:''')
open(p, "w", encoding="utf-8").write(s)

# 2) runtime Frame：saved 压栈后、sub 之前对齐
p2 = r"whiskerc/runtime_x64.py"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace(
    '''        for r in self.saved:
            a.push_r(r)
        self.patch_off = a.sub_rsp_placeholder()''',
    '''        for r in self.saved:
            a.push_r(r)
        a.align_rsp()               # 动态对齐：嵌套调用可能以未对齐 rsp 进入本函数
        self.patch_off = a.sub_rsp_placeholder()''')
open(p2, "w", encoding="utf-8").write(s2)

# 3) wkcc.wk：parseHandler/parseFunc 序言插 and rsp,-16；patchFrameSize 余量 +8
p3 = r"tools/wkcc.wk"
s3 = open(p3, encoding="utf-8").read()
old_ph = """        e8(85)                            # push rbp
        e8(72); e8(137); e8(229)          # mov rbp, rsp
        e8(72); e8(129); e8(236)"""
new_ph = """        e8(85)                            # push rbp
        e8(72); e8(137); e8(229)          # mov rbp, rsp
        e8(72); e8(131); e8(228); e8(240) # and rsp, -16（动态对齐：容忍未对齐调用入口）
        e8(72); e8(129); e8(236)"""
cnt = s3.count(old_ph)
s3 = s3.replace(old_ph, new_ph)
s3 = s3.replace(
    "        s2: Int = ((dmax + 24) / 16) * 16 + 8",
    "        s2: Int = ((dmax + 32) / 16) * 16 + 8   # +8 余量给 and rsp 的对齐损耗")
open(p3, "w", encoding="utf-8").write(s3)
print(f"wkcc 序言插入 {cnt} 处（parseHandler+parseFunc 应为 2）")
