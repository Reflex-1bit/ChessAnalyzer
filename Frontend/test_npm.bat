@echo off
echo Testing npm...
echo.
cd /d "%~dp0"
echo Current directory: %CD%
echo.
echo Testing npm run dev...
npm run dev
echo.
echo npm run dev finished with exit code: %ERRORLEVEL%
pause
