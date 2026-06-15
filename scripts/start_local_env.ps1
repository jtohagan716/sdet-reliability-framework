Write-Host "Starting SDET Reliability Framework local environment..." -ForegroundColor Cyan

Set-Location "C:\Users\James\Documents\sdet-reliability-framework"

Write-Host "Activating virtual environment..." -ForegroundColor Yellow
.\.venv\Scripts\Activate.ps1

Write-Host "Checking Python..." -ForegroundColor Yellow
python --version

Write-Host "Checking pytest..." -ForegroundColor Yellow
python -m pytest --version

Write-Host "Starting local FastAPI service on http://127.0.0.1:8000 ..." -ForegroundColor Green
python -m uvicorn api_service.app:app --reload