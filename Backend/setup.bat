@echo off
setlocal
chcp 65001 >nul
echo ========================================
echo   Chess Coach AI - Quick Setup
echo ========================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found!
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo.
    pause
    exit /b 1
)

echo Using:
python --version
echo.

:: Step 1: Create virtual environment
echo [1/5] Creating virtual environment...
if exist venv (
    echo Virtual environment already exists. Skipping...
) else (
    python -m venv venv
    if errorlevel 1 (
        echo [ERROR] Failed to create virtual environment
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
)

:: Step 2: Activate virtual environment
echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo [ERROR] Failed to activate virtual environment
    pause
    exit /b 1
)
echo ✓ Virtual environment activated

:: Step 3: Upgrade pip
echo [3/5] Upgrading pip...
python -m pip install --upgrade pip setuptools wheel --quiet
echo ✓ Pip upgraded

:: Step 4: Install dependencies (SQLite-first, no ML)
echo [4/5] Installing dependencies...
echo This may take a few minutes...
echo.
pip install -r requirements.txt
if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install some dependencies
    echo.
    pause
    exit /b 1
)
echo.
echo ✓ Dependencies installed

:: Step 5: Create .env file
echo [5/5] Setting up environment file...
if exist .env (
    echo .env file already exists. Skipping...
) else (
    if exist .env.example (
        copy .env.example .env >nul
        echo ✓ Created .env file from .env.example
        echo   Default uses SQLite: sqlite+aiosqlite:///./chess_coach.db
    ) else (
        echo [WARNING] .env.example not found. Creating basic .env...
        (
            echo # Database Configuration
            echo DATABASE_URL=sqlite+aiosqlite:///./chess_coach.db
            echo.
            echo # Stockfish Configuration
            echo STOCKFISH_PATH=C:\path\to\stockfish.exe
            echo STOCKFISH_DEPTH=15
            echo.
            echo # Security
            echo SECRET_KEY=change-this-secret-key-in-production
        ) > .env
        echo ✓ Created basic .env file
    )
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Run: run.bat    (or python main.py inside venv)
echo 2. Docs: http://localhost:8000/docs
echo.
pause
endlocal
