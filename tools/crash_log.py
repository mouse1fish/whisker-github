# -*- coding: utf-8 -*-
"""读 Windows 事件日志里 selfhost.exe 的崩溃记录（故障模块+偏移）。"""
import subprocess

PS = r"""
Get-WinEvent -FilterHashtable @{LogName='Application'; Id=1000} -MaxEvents 3 |
  ForEach-Object { ($_.Message -split "`n`r")[0..3] -join ' | ' }
"""
r = subprocess.run(["powershell", "-NoProfile", "-Command", PS],
                   capture_output=True, text=True, encoding="utf-8", errors="replace")
out = r.stdout or ""
print(out[:1500] if out.strip() else "(无崩溃记录)")
