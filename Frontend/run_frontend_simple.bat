@echo off
cd /d "%~dp0"
echo Starting frontend...
echo.
npm run dev
echo.
echo If you see this, the server stopped.
pause
