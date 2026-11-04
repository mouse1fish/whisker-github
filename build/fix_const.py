p = r"demos/3d/cube3d.wk"
s = open(p, encoding="utf-8").read()
s = s.replace("    FOCAL: Int = 700 * 65536       # 焦距", "    FOCAL: Int = 45875200          # 焦距 = 700 * 65536（字段初值须为字面量）")
s = s.replace("    CAMZ: Int = 4 * 65536          # 立方体中心 z", "    CAMZ: Int = 262144             # 立方体中心 z = 4 * 65536")
open(p, "w", encoding="utf-8").write(s)
print("常量预计算 OK")
