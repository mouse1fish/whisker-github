p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
old = '''    def runHeadless[n: Int] {
        i: Int = 0'''
new = '''    def runHeadless[n: Int] {
        print("fB0=", fB[0], " fG0=", fG[0], " fR0=", fR[0])
        spinX = 0
        spinY = 0
        transformAll()
        print("shade0=", faceShade(0), " shade1=", faceShade(1))
        print("ONE*30/100 =", ONE * 30 / 100)
        i: Int = 0'''
assert old in s
s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
