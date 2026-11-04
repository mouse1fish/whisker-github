p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
old = '''        fi4: Int = 0
        while fi4 < fldCount {
            if fldArrN[fi4] == 0 {
                e8(72); e8(199); e8(135)  # mov qword [rdi+disp32], imm32（48 C7 87）
                e32(fldOff[fi4])
                v4: Int = 0
                if fldHasInit[fi4] == 1 { v4 = fldInitVal[fi4] }
                e32(v4)
            }
            fi4 = fi4 + 1
        }'''
new = '''        fi4: Int = 0
        while fi4 < fldCount {
            if fldArrN[fi4] == 0 {
                if fldTy[fi4] == "Str" and fldHasInit[fi4] == 1 {
                    # 字符串字段初值是字面量：必须 RIP 相对 LEA（存的是运行期地址，
                    # 直接写 RVA 数值会得到不可解引用的偏移——2026-11-03 修复）
                    eLeaRcv(2, fldInitVal[fi4])          # lea rdx, [rip+disp32]
                    e8(72); e8(137); e8(151); e32(fldOff[fi4])   # mov [rdi+off32], rdx（48 89 97）
                } else {
                    e8(72); e8(199); e8(135)  # mov qword [rdi+disp32], imm32（48 C7 87）
                    e32(fldOff[fi4])
                    v4: Int = 0
                    if fldHasInit[fi4] == 1 { v4 = fldInitVal[fi4] }
                    e32(v4)
                }
            }
            fi4 = fi4 + 1
        }'''
assert old in s, "INIT 循环"
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("字符串字段初值修复完成")
