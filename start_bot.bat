@echo off
echo Starting Crypto Trading Bot Dashboard...
echo.

REM Activate virtual environment
call venv\Scripts\activate.bat

REM Check if database needs to be setup
echo Setting up database tables...
python setup_database.py

REM Start the dashboard
echo Starting web dashboard...
python start_dashboard.py

pause
