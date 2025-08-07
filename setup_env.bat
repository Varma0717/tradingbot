@echo off
echo Setting up Crypto Trading Bot environment...
echo.

:: Navigate to project directory
cd /d "c:\xampp\htdocs\application"

:: Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python is not installed or not in PATH
    echo Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo Python version:
python --version
echo.

:: Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

if errorlevel 1 (
    echo Error: Failed to activate virtual environment
    echo Recreating virtual environment...
    rmdir /s /q venv 2>nul
    python -m venv venv
    call venv\Scripts\activate.bat
)

:: Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

:: Install core dependencies first
echo.
echo Installing core dependencies...
pip install wheel setuptools

:: Install requirements
echo.
echo Installing project requirements...
pip install -r requirements.txt

:: Handle TA-Lib installation separately (if it fails)
echo.
echo Checking TA-Lib installation...
python -c "import talib" 2>nul
if errorlevel 1 (
    echo.
    echo TA-Lib not found. Installing TA-Lib...
    echo Note: TA-Lib requires Visual C++ Build Tools
    echo If installation fails, please install from:
    echo https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib
    echo.
    pip install TA-Lib
)

:: Create .env file if it doesn't exist
if not exist .env (
    echo.
    echo Creating .env file from template...
    copy .env.example .env
)

:: Test imports
echo.
echo Testing critical imports...
python -c "
try:
    import ccxt
    import pandas
    import numpy
    import fastapi
    import sqlalchemy
    print('✓ All critical packages imported successfully')
except ImportError as e:
    print(f'✗ Import error: {e}')
    exit(1)
"

if errorlevel 1 (
    echo.
    echo Some packages failed to import. Please check the error messages above.
    pause
    exit /b 1
)

echo.
echo ============================================
echo Environment setup completed successfully!
echo ============================================
echo.
echo To activate the environment manually, run:
echo   venv\Scripts\activate.bat
echo.
echo To start the dashboard, run:
echo   python run.py
echo.
echo To start the main bot, run:
echo   python main.py
echo.
pause
