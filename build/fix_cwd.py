# 1) wkcc.wk：blob 读取检查
p = r"tools/wkcc.wk"
s = open(p, encoding="utf-8").read()
old = '''        blob = alloc(RT_DATA_OFF + RT_DATA_LEN + 16)
        readBytes(blobPath, blob, RT_DATA_OFF + RT_DATA_LEN)'''
new = '''        blob = alloc(RT_DATA_OFF + RT_DATA_LEN + 16)
        bn: Int = readBytes(blobPath, blob, RT_DATA_OFF + RT_DATA_LEN)
        if bn < 0 {
            print("[wkcc] blob 读取失败: ", blobPath, "（CWD 需为项目根，或用第 3 参数指定）")
            return
        }'''
assert old in s, "blob 检查"; s = s.replace(old, new)
open(p, "w", encoding="utf-8").write(s)
print("wkcc blob 检查 OK")

# 2) wk.ps1：固定 CWD 到项目根
p2 = r"G:/trea-Eon-os/eonos/native/wk.ps1"
s2 = open(p2, encoding="utf-8").read()
old2 = '''$wkcc2 = Join-Path $wkTool "build\\wkcc2.exe"
Set-Location $PSScriptRoot'''
new2 = '''$wkcc2 = Join-Path $wkTool "build\\wkcc2.exe"
Set-Location $wkTool                    # blob 相对路径需要 CWD = 项目根'''
assert old2 in s2, "wk.ps1"; s2 = s2.replace(old2, new2)
open(p2, "w", encoding="utf-8").write(s2)
print("wk.ps1 CWD OK")

# 3) demos/3d/build.ps1：固定 CWD
p3 = r"G:/trea-Eon-os/trea-xiancheng-bianyiqi/demos/3d/build.ps1"
s3 = open(p3, encoding="utf-8").read()
old3 = '''Set-Location $PSScriptRoot'''
new3 = '''Set-Location $root                      # blob 相对路径需要 CWD = 项目根'''
assert old3 in s3, "build.ps1"; s3 = s3.replace(old3, new3)
open(p3, "w", encoding="utf-8").write(s3)
print("build.ps1 CWD OK")
