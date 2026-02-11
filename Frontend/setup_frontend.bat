@echo off
chcp 65001 >nul
title Frontend Setup
echo ========================================
echo   Chess Coach AI - Frontend Setup
echo ========================================
echo.

echo Checking for Node.js...
node --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Node.js not found!
  echo Please install Node.js 18+ from https://nodejs.org/
  echo.
  pause
  exit /b 1
)

echo Node.js version:
node --version
echo.

echo Checking for npm...
npm --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] npm not found!
  echo npm should come with Node.js installation
  echo.
  pause
  exit /b 1
)

echo npm version:
npm --version
echo.

echo Current directory:
cd
echo.

echo Installing dependencies...
echo This may take 5-10 minutes on first run...
echo.
npm install
set INSTALL_ERROR=%ERRORLEVEL%

if %INSTALL_ERROR% NEQ 0 (
  echo.
  echo ========================================
  echo [ERROR] Failed to install dependencies
  echo ========================================
  echo.
  echo Common issues:
  echo 1. Check your internet connection
  echo 2. Try: npm cache clean --force
  echo 3. Make sure you're in the project root folder
  echo.
  pause
  exit /b 1
)

echo.
echo ========================================
echo   Frontend Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Make sure backend is running: backend\run_py312.bat
echo 2. Start frontend: npm run dev
echo 3. Open: http://localhost:8080
echo.
pause
