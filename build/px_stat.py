d = open(r"build/3d_frame1.px","rb").read()
pts = [(240,180,"中心"), (300,150,"右上偏"), (180,220,"左下偏"), (240,60,"顶部")]
for x,y,tag in pts:
    o = (y*480+x)*4
    print(f"{tag} ({x},{y}): B={d[o]} G={d[o+1]} R={d[o+2]}")
# 全图颜色直方图（采样）
from collections import Counter
c = Counter()
for y in range(0,360,3):
    for x in range(0,480,3):
        o = (y*480+x)*4
        c[(d[o],d[o+1],d[o+2])] += 1
print("Top 颜色:", c.most_common(6))
