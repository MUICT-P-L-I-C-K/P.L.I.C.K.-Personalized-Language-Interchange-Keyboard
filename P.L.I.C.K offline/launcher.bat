@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   P.L.I.C.K. - Setup and Launch
echo ========================================
echo.

REM Check Python
python --version >nul 2>&1
if not %errorlevel% == 0 (
    echo ERROR: Python not found.
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during install.
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo Python %PYTHON_VERSION% found.
echo.

REM --------------------------------------------------------
REM Remove stale venv if it points to a different location
REM --------------------------------------------------------
if exist "%~dp0venv\pyvenv.cfg" (
    set "VENV_VALID=1"
    for /f "tokens=1,2,3" %%a in ('findstr /i "home" "%~dp0venv\pyvenv.cfg"') do set "VENV_HOME=%%c"
    if not exist "!VENV_HOME!\python.exe" set "VENV_VALID=0"

    if "!VENV_VALID!" == "0" (
        echo Old venv detected - removing...
        mkdir "%TEMP%\plick_empty" >nul 2>&1
        robocopy "%TEMP%\plick_empty" "%~dp0venv" /MIR /NFL /NDL /NJH /NJS /NC /NS >nul 2>&1
        rmdir /s /q "%~dp0venv" >nul 2>&1
        rmdir /s /q "%TEMP%\plick_empty" >nul 2>&1
        if exist "%~dp0venv" (
            echo ERROR: Could not remove old venv.
            echo Please delete the venv folder manually and try again.
            pause
            exit /b 1
        )
        echo Old venv removed.
        echo.
    ) else (
        echo Virtual environment is valid.
        echo.
    )
)

REM Create venv if missing
if not exist "%~dp0venv" (
    echo Creating virtual environment...
    python -m venv "%~dp0venv"
    if not %errorlevel% == 0 (
        echo ERROR: Failed to create virtual environment.
        pause
        exit /b 1
    )

    if not exist "%~dp0venv\Scripts\python.exe" (
        echo ERROR: venv was created but python.exe is missing.
        echo This happens with Microsoft Store Python.
        echo Please install Python from https://www.python.org/downloads/
        pause
        exit /b 1
    )
    echo Virtual environment created.
    echo.
)

set "PY=%~dp0venv\Scripts\python.exe"

REM Upgrade pip
echo Upgrading pip...
"%PY%" -m pip install --upgrade pip --quiet
echo pip ready.
echo.

REM Install dependencies
if not exist "%~dp0requirements.txt" (
    echo WARNING: requirements.txt not found - skipping.
    echo.
) else (
    echo Installing dependencies...
    echo.
    "%PY%" -m pip install -r "%~dp0requirements.txt"
    if not %errorlevel% == 0 (
        echo.
        echo ERROR: Failed to install dependencies.
        echo Please check your internet connection and try again.
        echo.
        pause
        exit /b 1
    )
    echo.
    echo Dependencies installed.

    REM Clear pip download cache to free up disk space
    echo Clearing pip cache to save disk space...
    "%PY%" -m pip cache purge >nul 2>&1
    echo Done.
    echo.
)

REM pywin32 post-install
if exist "%~dp0venv\Scripts\pywin32_postinstall.py" (
    echo Running pywin32 post-install...
    "%PY%" "%~dp0venv\Scripts\pywin32_postinstall.py" -install >nul 2>&1
    echo pywin32 ready.
    echo.
)

REM Check app entry point
if not exist "%~dp0app\main.py" (
    echo ERROR: app\main.py not found.
    echo Make sure launcher.bat is in the project root folder.
    pause
    exit /b 1
)

echo ========================================
echo   Setup complete - Launching P.L.I.C.K.
echo ========================================
echo.
echo App is starting. You can close this window.
echo.

set PYTHONIOENCODING=utf-8
start "" "%~dp0venv\Scripts\pythonw.exe" "%~dp0app\main.py"

endlocal
exit /b 0
