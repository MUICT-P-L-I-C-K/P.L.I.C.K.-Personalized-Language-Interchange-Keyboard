@echo off
setlocal enabledelayedexpansion

echo.
echo ========================================
echo   P.L.I.C.K. - Full Uninstall / Clean
echo ========================================
echo.
echo This will remove:
echo   - venv folder (Python environment)
echo   - languagetool_data folder (LanguageTool JAR)
echo   - __pycache__ folders (compiled Python cache)
echo   - settings.json (app settings)
echo   - pip download cache
echo   - pythainlp corpus data
echo.
set /p CONFIRM="Are you sure? Type YES to continue: "
if /i not "%CONFIRM%"=="YES" (
    echo Cancelled.
    pause
    exit /b 0
)
echo.

REM ── Remove venv ───────────────────────────────────────────────────────────
if exist "%~dp0venv" (
    echo Removing venv...
    mkdir "%TEMP%\plick_empty" >nul 2>&1
    robocopy "%TEMP%\plick_empty" "%~dp0venv" /MIR /NFL /NDL /NJH /NJS /NC /NS >nul 2>&1
    rmdir /s /q "%~dp0venv" >nul 2>&1
    rmdir /s /q "%TEMP%\plick_empty" >nul 2>&1
    if exist "%~dp0venv" (
        echo WARNING: Could not fully remove venv. Try restarting PC first then run again.
    ) else (
        echo venv removed.
    )
) else (
    echo venv not found, skipping.
)
echo.

REM ── Remove LanguageTool data ──────────────────────────────────────────────
if exist "%~dp0languagetool_data" (
    echo Removing languagetool_data...
    rmdir /s /q "%~dp0languagetool_data" >nul 2>&1
    echo languagetool_data removed.
) else (
    echo languagetool_data not found, skipping.
)
echo.

REM ── Remove settings.json ──────────────────────────────────────────────────
if exist "%~dp0settings.json" (
    echo Removing settings.json...
    del /f /q "%~dp0settings.json" >nul 2>&1
    echo settings.json removed.
) else (
    echo settings.json not found, skipping.
)
echo.

REM ── Remove __pycache__ folders ────────────────────────────────────────────
echo Removing __pycache__ folders...
for /d /r "%~dp0" %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" >nul 2>&1
    )
)
echo __pycache__ folders removed.
echo.

REM ── Remove LanguageTool temp files in system temp ─────────────────────────
echo Removing LanguageTool temp files...
for /d %%d in ("%LOCALAPPDATA%\Temp\LanguageTool*") do (
    if exist "%%d" (
        rmdir /s /q "%%d" >nul 2>&1
    )
)
echo LanguageTool temp files removed.
echo.

REM ── Clear pip download cache ──────────────────────────────────────────────
echo Clearing pip download cache...
python -m pip cache purge >nul 2>&1
echo pip cache cleared.
echo.

REM ── Remove pythainlp corpus data ──────────────────────────────────────────
set "THAI_DATA=%APPDATA%\pythainlp-data"
if exist "%THAI_DATA%" (
    echo Removing pythainlp corpus data...
    echo Location: %THAI_DATA%
    rmdir /s /q "%THAI_DATA%" >nul 2>&1
    echo pythainlp data removed.
) else (
    echo pythainlp data not found, skipping.
)
echo.

echo ========================================
echo   Uninstall complete!
echo ========================================
echo.
echo Everything has been removed. To reinstall:
echo   1. Double-click launcher.bat
echo   2. Wait for setup to complete
echo   3. App will launch automatically
echo.
pause
