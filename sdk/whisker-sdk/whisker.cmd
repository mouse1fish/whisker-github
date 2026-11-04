@echo off
rem Whisker SDK wrapper (Windows cmd). CLI: wkcc2 <src> <out> [blob]
chcp 65001 >nul
if /i "%~1"=="version" (echo Whisker SDK ^(self-hosted compiler wkcc2^)& exit /b 0)
if /i not "%~1"=="compile" (
    echo Usage: whisker compile input.wk [output.exe]
    exit /b 1
)
set "SRC=%~2"
if "%~2"=="" (
    echo Usage: whisker compile input.wk [output.exe]
    exit /b 1
)
if "%~3"=="" (set "OUT=%~n2.exe") else set "OUT=%~3"
if not exist "%SRC%" (
    echo Error: not found: %SRC%
    exit /b 1
)
"%~dp0bin\wkcc2.exe" "%SRC%" "%OUT%" "%~dp0share\rt_blob.bin"
if errorlevel 1 (
    echo Error: compilation failed
    exit /b 1
)
echo OK: %OUT%
exit /b 0