p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
old = s[s.index("    # ============ 输出：BMP 落盘（无头模式）============"):s.index("    def runHeadless[n: Int] {")]
new = '''    # ============ 输出：原始帧落盘（无头模式，便于自动化校验）============
    def saveRaw[path: Str] {
        writeBytes(path, fb, W * H * 4)
        print("[3d] ", path, " ", W, "x", H)
    }

'''
s = s.replace(old, new)
s = s.replace('            saveBmp(strCat(strCat("build/3d_frame", intToStr(i)), ".bmp"))',
              '            saveRaw(strCat(strCat("build/3d_frame", intToStr(i)), ".px"))')
open(p, "w", encoding="utf-8").write(s)
print("saveRaw 替换完成")
