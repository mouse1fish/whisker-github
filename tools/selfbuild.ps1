# Whisker 自举构建脚本（Windows PowerShell 版）
#
# 用法（从项目根目录）:
#   powershell -File tools\selfbuild.ps1              自举构建 wkcc.wk 本身（收敛校验 + hello 冒烟）
#   powershell -File tools\selfbuild.ps1 目标.wk [out] 用 wkcc2 编译任意源文件（CLI 传参）
#
# 若 wkcc2 损坏，用应急链重建:
#   python -m whiskerc build tools\wkcc.wk
#   copy tools\wkcc.wk build\lex_input.txt（或直接: build\wkcc.exe tools\wkcc.wk build\selfhost.exe）
#   copy build\selfhost.exe build\wkcc2.exe
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$WKC2 = "build\wkcc2.exe"
if (-not (Test-Path $WKC2)) {
    Write-Error "[selfbuild] 错误: $WKC2 不存在，请先用应急链重建（见脚本头注释）"
    exit 1
}

if ($args.Count -ge 1) {
    $src = $args[0]
    $out = if ($args.Count -ge 2) { $args[1] } else { "build\out.exe" }
    & $WKC2 $src $out
    if ($LASTEXITCODE -ne 0) { Write-Error "[selfbuild] 编译失败: $src"; exit 1 }
    Write-Host "[selfbuild] OK: $src -> $out"
    exit 0
}

# 自举构建: wkcc2 编译 wkcc.wk 自身（CLI 传参）
& $WKC2 "tools\wkcc.wk" "build\selfhost.exe"
if ($LASTEXITCODE -ne 0) { Write-Error "[selfbuild] 自举编译失败"; exit 1 }
if ((Get-FileHash $WKC2).Hash -eq (Get-FileHash "build\selfhost.exe").Hash) {
    Write-Host "[selfbuild] 自举收敛确认: 产物与 wkcc2.exe 逐字节一致 (fixpoint)"
} else {
    Write-Error "[selfbuild] 错误: 产物与 wkcc2.exe 不一致（编出自身应当逐字节相同）"
    exit 1
}
# hello 冒烟
& $WKC2 "examples\hello.wk" "build\hello_smoke.exe" | Out-Null
$out = & "build\hello_smoke.exe"
if ("$out" -match "Whisker") {
    Write-Host "[selfbuild] 冒烟测试通过: hello 输出正常"
} else {
    Write-Error "[selfbuild] 错误: hello 冒烟测试失败"
    exit 1
}