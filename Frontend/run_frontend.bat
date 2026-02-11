@echo off
chcp 65001 >nul
title Frontend Dev Server
echo ========================================
echo   Starting Frontend Dev Server
echo ========================================
echo.

if not exist node_modules (
  echo [ERROR] Dependencies not installed!
  echo Run setup_frontend.bat first
  echo.
  pause
  exit /b 1
)

echo Frontend will be available at:
echo   - http://localhost:8080
echo.
echo Backend should be running at:
echo   - http://localhost:8000
echo.
echo Starting server...
echo.

npm run dev
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% NEQ 0 (
  echo.
  echo ========================================
  echo [ERROR] Dev server failed (exit code: %EXIT_CODE%)
  echo ========================================
  echo.
  echo Check error messages above
  echo.
)

pause
