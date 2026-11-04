$ErrorActionPreference = "Stop"
$root = "G:\trea-Eon-os\trea-xiancheng-bianyiqi"
Set-Location $root
$src = "$root\demos\3d\cube3d_par.wk"
$out = "$root\demos\3d\cube3d_par.exe"
& "$root\build\wkcc2.exe" $src $out
if ($LASTEXITCODE -ne 0) { Write-Error "编译失败"; exit 1 }
Write-Host "[3d-par] OK: $out"
