# 1) runtime_x64.py Frame.size：16 对齐（and rsp 后 rsp 恒为 16 对齐，sub 量也须 16 对齐）
p = r"whiskerc/runtime_x64.py"
s = open(p, encoding="utf-8").read()
old = '''        f = 32 + 8 * self.nextra + 8 * self.nslots
        want = (8 * len(self.saved)) % 16
        while f % 16 != want:
            f += 8
        return f'''
new = '''        f = 32 + 8 * self.nextra + 8 * self.nslots
        # 2026-11-02：序言已 and rsp,-16（rsp 恒 16 对齐），sub 量须为 16 的倍数，
        # 否则帧内调用点 rsp≡8（奇偶校验旧逻辑在动态对齐下反而制造未对齐）
        return (f + 15) // 16 * 16'''
if old in s:
    s = s.replace(old, new)
    print("Frame.size 已改 16 对齐")
else:
    print("!! Frame.size 未匹配")
open(p, "w", encoding="utf-8").write(s)

# 2) wkcc.wk patchFrameSize：s2 改 16 对齐
p2 = r"tools/wkcc.wk"
s2 = open(p2, encoding="utf-8").read()
s2 = s2.replace(
    "        s2: Int = ((dmax + 32) / 16) * 16 + 8   # +8 余量给 and rsp 的对齐损耗",
    "        s2: Int = ((dmax + 47) / 16) * 16       # and rsp,-16 后 sub 量须 16 对齐（含对齐损耗余量）")
open(p2, "w", encoding="utf-8").write(s2)
print("wkcc patchFrameSize 已改 16 对齐")
