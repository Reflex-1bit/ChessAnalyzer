@echo off
chcp 65001 >nul
echo ========================================
echo   Chess Coach AI - Setup (Python 3.12)
echo ========================================
echo.

py -3.12 --version >nul 2>&1
if errorlevel 1 (
  echo [ERROR] Python 3.12 not found
  echo Install Python 3.12: winget install --id Python.Python.3.12 -e
  pause
  exit /b 1
)

echo Using:
py -3.12 --version
echo.

echo Creating virtual environment...
if exist venv312 (
  echo venv312 already exists. Skipping...
) else (
  py -3.12 -m venv venv312
  if errorlevel 1 (
    echo [ERROR] Failed to create venv312
    pause
    exit /b 1
  )
)

call venv312\Scripts\activate.bat
if errorlevel 1 (
  echo [ERROR] Failed to activate venv312
  pause
  exit /b 1
)

echo Upgrading pip...
python -m pip install --upgrade pip setuptools wheel --quiet

echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
  echo [ERROR] Dependencies failed to install
  pause
  exit /b 1
)

echo Setting up .env file...
if not exist .env (
  if exist .env.example (
    copy .env.example .env >nul
    echo Created .env from .env.example
  )
)

echo.
echo Setup complete!
echo Next: run run_py312.bat
echo.
pause
