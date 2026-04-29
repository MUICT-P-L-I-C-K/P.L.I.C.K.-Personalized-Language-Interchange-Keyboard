@echo off
setlocal
set PYTHONIOENCODING=utf-8
"%~dp0venv\Scripts\python.exe" "%~dp0app\main.py"
pause
endlocal