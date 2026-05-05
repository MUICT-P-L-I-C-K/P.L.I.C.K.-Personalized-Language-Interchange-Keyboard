@echo off
chcp 65001 >nul
color 0A

echo.
echo ========================================
echo  P.L.I.C.K. Setting - Auto Setup
echo ========================================
echo.

REM ========================================
REM Check if Python is installed
REM ========================================
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found!
    echo.
    echo Please install Python first:
    echo 📥 https://www.python.org/downloads/
    echo.
    echo ⚠️  During installation, CHECK the box:
    echo    "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Python %PYTHON_VERSION% found!
echo.

REM ========================================
REM Check if Java is installed (required for LanguageTool)
REM ========================================
echo 🔍 Checking for Java...
java -version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Java command not found in PATH.
    echo � Searching for existing Java installation...
    
    REM Check common Java paths
    if exist "C:\Program Files\Microsoft\jdk-17.0.4.101-hotspot\bin\java.exe" (
        echo ✅ Found Java at standard path!
        set "JAVA_HOME=C:\Program Files\Microsoft\jdk-17.0.4.101-hotspot"
        set "PATH=%PATH%;C:\Program Files\Microsoft\jdk-17.0.4.101-hotspot\bin"
        goto :JAVA_found
    )
    
    REM Try generic search in Program Files
    for /d %%i in ("C:\Program Files\Java\jdk*") do (
        if exist "%%i\bin\java.exe" (
             echo ✅ Found Java at %%i
             set "PATH=%PATH%;%%i\bin"
             goto :JAVA_found
        )
    )
    
    for /d %%i in ("C:\Program Files\Microsoft\jdk*") do (
        if exist "%%i\bin\java.exe" (
             echo ✅ Found Microsoft JDK at %%i
             set "PATH=%PATH%;%%i\bin"
             goto :JAVA_found
        )
    )

    echo.
    echo 📦 Attempting to install/update Java via winget...
    
    winget install -e --id Microsoft.OpenJDK.17 --accept-source-agreements --accept-package-agreements
    
    REM Winget sometimes returns non-zero even if "already installed" or "no upgrade".
    REM So we re-check manually for the file.
    
    echo.
    echo 🔄 Re-checking for installed Java...
    
    REM Try to find it again after potential install
    for /d %%i in ("C:\Program Files\Microsoft\jdk*") do (
        if exist "%%i\bin\java.exe" (
             echo ✅ Java installation confirmed at %%i
             set "PATH=%PATH%;%%i\bin"
             goto :JAVA_found
        )
    )
    
    REM Last attempt check
    java -version >nul 2>&1
    if %errorlevel% neq 0 (
        echo.
        echo ❌ Java still not detected.
        echo It might differ based on system. Please restart computer or install manually.
        echo 📥 https://adoptium.net/
        echo.
        pause
        exit /b 1
    )
) else (
    echo ✅ Java found in PATH!
)

:JAVA_found
echo.
REM Refresh environment explicitly if possible (optional but helpful)
call refreshenv >nul 2>&1 

REM ========================================
REM Create/Use Virtual Environment
REM ========================================
cd /d "%~dp0Backend"

if not exist "venv" (
    echo 📁 Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ❌ Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✅ Virtual environment created!
) else (
    echo ✅ Virtual environment exists
)
echo.

REM ========================================
REM Install dependencies using venv pip
REM ========================================
echo 📦 Checking/Installing dependencies...
echo.

call venv\Scripts\python.exe -m pip install --upgrade pip
call venv\Scripts\python.exe -m pip install -r "%~dp0requirements.txt"

if %errorlevel% neq 0 (
    echo.
    echo ❌ Failed to install dependencies
    echo Please check your internet connection and try again
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ Installation complete!
echo.
echo ========================================
echo  🚀 Starting Server...
echo ========================================
echo.
echo ℹ️  Keep this window open while using the extension
echo ℹ️  Server running at: http://localhost:8000
echo.

set PYTHONIOENCODING=utf-8
call venv\Scripts\python.exe server.py

echo.
echo ❌ Server stopped or error occurred
echo Please check the error message above
pause
