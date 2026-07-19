$ErrorActionPreference = "Stop"

Write-Host "Container status:"
docker compose ps

Write-Host "`nLiveness:"
Invoke-RestMethod http://localhost:8000/health/live | ConvertTo-Json

Write-Host "`nReadiness:"
Invoke-RestMethod http://localhost:8000/health/ready | ConvertTo-Json

Write-Host "`nAPI root:"
Invoke-RestMethod http://localhost:8000/ | ConvertTo-Json
