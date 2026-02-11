@echo off
chcp 65001 >nul
echo ========================================
echo   Chess Coach AI - Quick Start Mode
echo   ^(No database required for testing^)
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo Installing minimal dependencies (FastAPI 0.68 with Pydantic v1 for Python 3.14)...
pip install "fastapi==0.68.2" "pydantic==1.10.13" uvicorn python-dotenv --quiet

if errorlevel 1 (
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo Starting minimal server...
echo.
echo Server will be available at:
echo   - API: http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo   - Health: http://localhost:8000
echo.
echo This is a minimal version without database/ML features.
echo Run setup.bat for full functionality.
echo.
echo Press Ctrl+C to stop the server
echo.
echo ========================================
echo.

python -c "from fastapi import FastAPI; import uvicorn; app = FastAPI(); app.get('/')(lambda: {'status': 'running', 'mode': 'quick-start'}); uvicorn.run(app, host='0.0.0.0', port=8000)"

pause
