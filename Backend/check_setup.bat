@echo off
chcp 65001 >nul
echo ========================================
echo   Chess Coach AI - Setup Checker
echo ========================================
echo.

set ERRORS=0

:: Check Python
echo [Checking] Python...
python --version >nul 2>&1
if errorlevel 1 (
    echo   ✗ Python not found
    set /a ERRORS+=1
) else (
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
    echo   ✓ Python %PYTHON_VERSION% found
)

:: Check virtual environment
echo [Checking] Virtual environment...
if exist venv (
    echo   ✓ Virtual environment exists
) else (
    echo   ✗ Virtual environment not found
    set /a ERRORS+=1
)

:: Check .env file
echo [Checking] Environment file...
if exist .env (
    echo   ✓ .env file exists
) else (
    echo   ✗ .env file not found
    set /a ERRORS+=1
)

:: Check dependencies
if exist venv (
    echo [Checking] Python dependencies...
    call venv\Scripts\activate.bat >nul 2>&1
    python -c "import fastapi" >nul 2>&1
    if errorlevel 1 (
        echo   ✗ Dependencies not installed
        set /a ERRORS+=1
    ) else (
        echo   ✓ Dependencies installed
    )
)

:: Summary
echo.
echo ========================================
if %ERRORS% EQU 0 (
    echo   Setup looks good!
    echo   You can run the application with: run.bat
) else (
    echo   Found %ERRORS% issue^(s^)
    echo   Please run setup.bat to fix them
)
echo ========================================
echo.
pause
