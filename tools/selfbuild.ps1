# Whisker 自举构建脚本（Windows PowerShell 版，与 tools/selfbuild.sh 等价）
#
# 用法（必须从项目根目录运行）:
#   powershell -File tools\selfbuild.ps1          # 自举构建 wkcc.wk 本身（收敛校验 + hello 冒烟）
#   powershell -File tools\selfbuild.ps1 目标.wk  # 用 wkcc2 编译任意 Whisker 源文件
#
# 前置条件: build\wkcc2.exe 存在（自举链已建立）
# 若 wkcc2 损坏，用应急链重建:
#   python -m whiskerc build tools\wkcc.wk        # -> build\wkcc.exe
#   copy tools\wkcc.wk build\lex_input.txt
#   python tools\run_pe_test.py build\wkcc.exe    # -> build\selfhost.exe
#   copy build\selfhost.exe build\wkcc2.exe
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$WKC2 = "build\wkcc2.exe"
if (-not (Test-Path $WKC2)) {
    Write-Error "[selfbuild] 错误: $WKC2 不存在，请先用应急链重建（见脚本头注释）"
    exit 1
}

function Invoke-Wkcc2 {
    # 运行 wkcc2（当前 lex_input.txt 已就位）；Windows 下新 exe 可能被杀毒短暂锁定，重试一次
    & .\build\wkcc2.exe | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Start-Sleep -Milliseconds 300
        & .\build\wkcc2.exe | Out-Null
    }
    return $LASTEXITCODE
}

if ($args.Count -ge 1) {
    # ---- 普通构建: wkcc2 编译用户目标 ----
    Copy-Item $args[0] build\lex_input.txt -Force
    $rc = Invoke-Wkcc2
    if ($rc -ne 0) { Write-Error "[selfbuild] 编译失败: $($args[0])"; exit 1 }
    Write-Host "[selfbuild] OK: $($args[0]) -> build\selfhost.exe"
    exit 0
}

# ---- 自举构建: wkcc2 编译 wkcc.wk 自身 ----
Copy-Item tools\wkcc.wk build\lex_input.txt -Force
$rc = Invoke-Wkcc2
if ($rc -ne 0) { Write-Error "[selfbuild] 自举编译失败"; exit 1 }

if ((Get-FileHash $WKC2).Hash -eq (Get-FileHash "build\selfhost.exe").Hash) {
    Write-Host "[selfbuild] 自举收敛确认: 产物与 wkcc2.exe 逐字节一致 (fixpoint)"
} else {
    Write-Warning "[selfbuild] 产物与 wkcc2.exe 不一致，再迭代一轮..."
    Copy-Item build\selfhost.exe $WKC2 -Force
    Copy-Item tools\wkcc.wk build\lex_input.txt -Force
    $rc = Invoke-Wkcc2
    if ((Get-FileHash $WKC2).Hash -eq (Get-FileHash "build\selfhost.exe").Hash) {
        Write-Host "[selfbuild] 第二轮收敛"
    } else {
        Write-Error "[selfbuild] 错误: 两轮后仍未收敛，wkcc2 可能有 bug"
        exit 1
    }
}

# ---- 冒烟测试: hello 闭环 ----
Copy-Item examples\hello.wk build\lex_input.txt -Force
$rc = Invoke-Wkcc2
$out = & .\build\selfhost.exe
if ("$out" -match "Whisker") {
    Write-Host "[selfbuild] 冒烟测试通过: hello 输出正常"
} else {
    Write-Error "[selfbuild] 错误: hello 冒烟测试失败"
    exit 1
}
