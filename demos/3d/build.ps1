# cube3d 构建：拼接引擎与场景（单 actor），wkcc2 CLI 直调
$ErrorActionPreference = "Stop"
$root = "G:\trea-Eon-os\trea-xiancheng-bianyiqi"
Set-Location $PSScriptRoot
$src = Get-Content cube3d.wk -Encoding UTF8 -Raw
$inc = Get-Content ..\..\whisker-github-tmp.inc -ErrorAction SilentlyContinue
# 无拼接需求：cube3d.wk 自包含，直接 CLI
& "$root\build\wkcc2.exe" cube3d.wk cube3d.exe
if ($LASTEXITCODE -ne 0) { Write-Error "编译失败"; exit 1 }
Write-Host "[3d] OK: cube3d.exe"