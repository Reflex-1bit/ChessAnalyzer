@echo off
chcp 65001 >nul
title Chess Coach AI Server
echo ========================================
echo   Starting Chess Coach AI (Python 3.12)
echo ========================================
echo.

if not exist venv312 (
  echo [ERROR] venv312 not found. Run setup_py312.bat first.
  pause
  exit /b 1
)

echo Checking for processes using port 8000...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
  echo Killing process %%a using port 8000...
  taskkill /F /PID %%a >nul 2>&1
)

call venv312\Scripts\activate.bat
if errorlevel 1 (
  echo [ERROR] Failed to activate venv312
  pause
  exit /b 1
)

echo.
echo Server will be available at:
echo   - API:  http://localhost:8000
echo   - Docs: http://localhost:8000/docs
echo   - Health: http://localhost:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.
echo Starting server...
echo.

python main.py 2>&1
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% NEQ 0 (
  echo.
  echo ========================================
  echo [ERROR] Server failed to start (exit code: %EXIT_CODE%)
  echo ========================================
  echo.
  echo Check the error messages above.
  echo.
)

pause
