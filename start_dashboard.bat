@echo off
echo Starting Crypto Trading Bot Dashboard...
echo.

:: Navigate to project directory
cd /d "c:\xampp\htdocs\application"

:: Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo Virtual environment not found!
    echo Please run setup_env.bat first
    pause
    exit /b 1
)

:: Activate virtual environment
call venv\Scripts\activate.bat

:: Check if requirements are installed
python -c "import fastapi" 2>nul
if errorlevel 1 (
    echo FastAPI not found! Installing requirements...
    pip install -r requirements.txt
)

:: Start the dashboard
echo Starting dashboard on http://localhost:8000
echo Press Ctrl+C to stop the server
echo.
python run_dashboard.py

pause
