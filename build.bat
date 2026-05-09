@echo off
setlocal enabledelayedexpansion
cd /d "%~dp0"

echo ============================================================
echo    Local Billing Tool - One-Click Encrypted Build
echo ============================================================
echo.

:: ---- detect Python ----
set "PYTHON_EXE="

:: 1. try current session (conda env / venv already activated)
where python >nul 2>&1
if %errorlevel% equ 0 (
    for /f "delims=" %%i in ('where python 2^>nul') do (
        if exist "%%i" (
            set "PYTHON_EXE=%%i"
            goto :found
        )
    )
)

:: 2. read from .vscode/settings.json via PowerShell
if exist ".vscode\settings.json" (
    for /f "delims=" %%i in ('powershell -NoProfile -Command "try { $j = Get-Content '.vscode\settings.json' -Raw | ConvertFrom-Json; Write-Output $j.'python.defaultInterpreterPath' } catch {}" 2^>nul') do (
        set "RAW=%%i"
        set "RAW=!RAW: =!"
        set "RAW=!RAW:"=!"
        if exist "!RAW!" set "PYTHON_EXE=!RAW!"
    )
)

:: 3. check common Anaconda paths
if "%PYTHON_EXE%"=="" (
    for %%d in (E: D: C:) do (
        if exist "%%d\anaconda3\python.exe"           set "PYTHON_EXE=%%d\anaconda3\python.exe"
        if exist "%%d\anaconda3\envs\env_python39\python.exe" set "PYTHON_EXE=%%d\anaconda3\envs\env_python39\python.exe"
        if exist "%%d\Python39\python.exe"            set "PYTHON_EXE=%%d\Python39\python.exe"
        if exist "%%d\Python310\python.exe"           set "PYTHON_EXE=%%d\Python310\python.exe"
        if exist "%%d\Python38\python.exe"            set "PYTHON_EXE=%%d\Python38\python.exe"
    )
)

:found
if "%PYTHON_EXE%"=="" (
    echo [ERROR] Python not found. Please install Python 3.8-3.10.
    pause
    exit /b 1
)

echo   Python: %PYTHON_EXE%
echo.

"%PYTHON_EXE%" build.py

set "BUILD_ERROR=%errorlevel%"

:: ---- 清理打包中间文件 ----
echo.
echo ============================================================
echo    Cleaning intermediate build files...
echo ============================================================

if exist "build_temp\" (
    rmdir /s /q "build_temp" 2>nul
    echo   Deleted: build_temp/
)
if exist "build\" (
    rmdir /s /q "build" 2>nul
    echo   Deleted: build/
)
if exist "dist\" (
    rmdir /s /q "dist" 2>nul
    echo   Deleted: dist/
)
for /d %%d in (*.egg-info) do (
    rmdir /s /q "%%d" 2>nul
    echo   Deleted: %%d/
)
for %%f in (*.spec) do (
    del /f /q "%%f" 2>nul
    echo   Deleted: %%~nxf
)
for /r /d %%d in (__pycache__) do (
    if exist "%%d" (
        rmdir /s /q "%%d" 2>nul
    )
)

for /r %%f in (*.pyd) do (
    del /f /q "%%f" 2>nul
)
for /r %%f in (*.c) do (
    del /f /q "%%f" 2>nul
)

echo   Cleanup complete.
echo.

if %BUILD_ERROR% neq 0 (
    echo [ERROR] Build failed. See output above.
)
pause
exit /b %BUILD_ERROR%
