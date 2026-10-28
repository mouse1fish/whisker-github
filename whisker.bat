@echo off
REM Whisker compiler launcher: whisker check|emit|build|run <file.whisker>
cd /d "%~dp0"
python -m whiskerc %*
exit /b %ERRORLEVEL%