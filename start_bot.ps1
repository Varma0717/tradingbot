# PowerShell script to start the Crypto Trading Bot Dashboard

Write-Host "Starting Crypto Trading Bot Dashboard..." -ForegroundColor Green
Write-Host ""

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& ".\venv\Scripts\Activate.ps1"

# Setup database
Write-Host "Setting up database tables..." -ForegroundColor Yellow
python setup_database.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Database setup completed successfully!" -ForegroundColor Green
    
    # Start dashboard
    Write-Host "Starting web dashboard..." -ForegroundColor Yellow
    python start_dashboard.py
}
else {
    Write-Host "Database setup failed. Please check your MySQL connection." -ForegroundColor Red
    Read-Host "Press Enter to exit"
}
