@echo off
rem Whisker SDK wrapper (Windows cmd). ASCII only + chcp 65001 (see project history).
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
rem wkcc2 reads ./build/lex_input.txt + ./build/rt_blob.bin relative to CWD,
rem so run it inside an isolated temp build dir and ship the result back.
set "TD=%TEMP%\whisker-%RANDOM%%RANDOM%"
mkdir "%TD%\build" 2>nul
if errorlevel 1 (echo Error: cannot create temp dir& exit /b 1)
copy /y "%~dp0share\rt_blob.bin" "%TD%\build\rt_blob.bin" >nul
copy /y "%SRC%" "%TD%\build\lex_input.txt" >nul
pushd "%TD%"
call "%~dp0bin\wkcc2.exe"
set "RC=%ERRORLEVEL%"
popd
if not "%RC%"=="0" (
    echo Error: compilation failed ^(see [wkcc] lines above^)
    rd /s /q "%TD%" 2>nul
    exit /b 1
)
copy /y "%TD%\build\selfhost.exe" "%OUT%" >nul
rd /s /q "%TD%" 2>nul
echo OK: %OUT%
exit /b 0
