import re
p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
updates = {
    "OFF_NET_ACCEPT": 3715, "OFF_NET_CONNECT": 3743, "OFF_NET_SEND": 3901,
    "OFF_NET_RECV": 3929, "OFF_NET_CLOSE": 3957, "OFF_PROC_SPAWN": 3982,
    "OFF_PROC_SPAWN_N": 4469, "OFF_PROC_READ": 4477, "OFF_PROC_WAIT": 4590,
    "OFF_PROC_FREE": 4675,
    "RT_TEXT_LEN": 4742, "RT_DATA_LEN": 17992, "RT_DATA_OFF": 5658,
    "IAT_RVA": 218424, "IAT_IN_DATA": 17720,
}
for k, v in updates.items():
    pat = re.compile(rf"^(\s*{k}:\s*Int\s*=\s*)(\d+)", re.M)
    m = pat.search(s)
    if not m:
        print(f"!! 未找到 {k}")
        continue
    old = m.group(2)
    s = pat.sub(lambda mm: mm.group(1) + str(v), s, count=1)
    print(f"{k}: {old} -> {v}")
open(p, "w", encoding="utf-8").write(s)
