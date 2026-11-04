@echo off
REM ============================================================
REM  Whisker build wrapper (M0) -- compiles generated C + runtime with MSVC
REM  usage:  tools\build.bat /Fe:xxx.exe ..\build\app.c ..\runtime\whisker_runtime.c
REM  run from project root; cwd switches to build\, artifacts land in build\
REM  If compiler / SDK move, edit the three WHISKER_* vars below only.
REM ============================================================
chcp 65001 > nul

set "WHISKER_VCVARS=E:\visual studio\VC\Auxiliary\Build\vcvarsall.bat"
set "WHISKER_SDK_ROOT=G:\cursor--steamfabu-weidu\winsdk"
set "WHISKER_SDK_VER=10.0.28000.0"

cd /d "%~dp0.."
if not exist build mkdir build

call "%WHISKER_VCVARS%" x64 > nul 2>&1
if errorlevel 1 (echo [whisker] vcvarsall failed: %WHISKER_VCVARS% & exit /b 1)

set "INCLUDE=%WHISKER_SDK_ROOT%\extracted\c\Include\%WHISKER_SDK_VER%\um;%WHISKER_SDK_ROOT%\extracted\c\Include\%WHISKER_SDK_VER%\shared;%WHISKER_SDK_ROOT%\extracted\c\Include\%WHISKER_SDK_VER%\ucrt;%INCLUDE%"
set "LIB=%WHISKER_SDK_ROOT%\extracted_x64\c\um\x64;%WHISKER_SDK_ROOT%\extracted_x64\c\ucrt\x64;%LIB%"
set "PATH=%WHISKER_SDK_ROOT%\extracted\c\bin\%WHISKER_SDK_VER%\x64;%PATH%"

pushd build
cl /nologo /utf-8 /std:c11 /O2 /W3 /I"..\runtime" %* /link kernel32.lib
set "RC=%ERRORLEVEL%"
popd
exit /b %RC%