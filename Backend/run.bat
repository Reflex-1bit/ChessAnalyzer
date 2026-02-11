@echo off
chcp 65001 >nul
echo ========================================
echo   Starting Chess Coach AI Backend
echo ========================================
echo.

:: Check if virtual environment exists
if not exist venv (
    echo [ERROR] Virtual environment not found!
    echo Please run setup.bat first
    echo.
    pause
    exit /b 1
)

:: Check if .env exists
if not exist .env (
    echo [WARNING] .env file not found!
    echo Creating basic .env file...
    if exist .env.example (
        copy .env.example .env >nul
    )
    echo Please edit .env with your settings before continuing.
    echo.
    pause
)

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

:: Check if dependencies are installed
python -c "import fastapi" >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Dependencies not installed!
    echo Please run setup.bat first
    echo.
    pause
    exit /b 1
)

echo Starting server...
echo.
echo Server will be available at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo   - Health: http://localhost:8000
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

:: Run the application
python main.py
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to start server
    echo Check the error message above
    echo.
    pause
    exit /b 1
)

pause
