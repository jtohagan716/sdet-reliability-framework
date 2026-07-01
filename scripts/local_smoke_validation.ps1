# Local Smoke Validation Script
# SDET Reliability Framework
#
# Purpose:
# Runs a focused local validation pass against the Docker-based API stack.
# This script validates service health, key REST API behavior, focused Pytest coverage,
# and Postman/Newman API coverage.

$ErrorActionPreference = "Stop"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "=== $Message ==="
}

function Fail-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "FAILED: $Message" -ForegroundColor Red
    exit 1
}

Write-Step "Starting Docker Compose stack"
docker compose up -d --build

Write-Step "Checking running containers"
docker ps

Write-Step "Waiting for API health endpoint"

$healthOk = $false

for ($i = 1; $i -le 20; $i++) {
    try {
        $health = Invoke-RestMethod http://localhost:8000/health
        if ($health.status -eq "UP") {
            $healthOk = $true
            Write-Host "API health check passed."
            break
        }
    }
    catch {
        Start-Sleep -Seconds 2
    }
}

if (-not $healthOk) {
    Write-Host "API health check did not pass. Showing API container logs..."
    docker logs sdet-reliability-api
    Fail-Step "API health endpoint did not return UP"
}

Write-Step "Validating synthetic patient endpoint: GET /patients/1001"

$patient = Invoke-RestMethod http://localhost:8000/patients/1001

if ($patient.patient_id -ne 1001) {
    Fail-Step "Expected patient_id 1001"
}

if ($patient.status -ne "active") {
    Fail-Step "Expected patient status active"
}

Write-Host "Valid patient check passed."

Write-Step "Validating missing patient returns 404"

try {
    Invoke-RestMethod http://localhost:8000/patients/9999
    Fail-Step "Expected 404 for missing patient, but request succeeded"
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -ne 404) {
        Fail-Step "Expected 404 for missing patient, got $statusCode"
    }
}

Write-Host "Missing patient 404 check passed."

Write-Step "Validating invalid patient id returns 422"

try {
    Invoke-RestMethod http://localhost:8000/patients/abc
    Fail-Step "Expected 422 for invalid patient id, but request succeeded"
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    if ($statusCode -ne 422) {
        Fail-Step "Expected 422 for invalid patient id, got $statusCode"
    }
}

Write-Host "Invalid patient id 422 check passed."

Write-Step "Running focused Pytest REST API tests"
python -m pytest tests\test_synthetic_patient_api.py -q

if ($LASTEXITCODE -ne 0) {
    Fail-Step "Focused Pytest REST API tests failed"
}

Write-Step "Running Postman/Newman API tests"
npm run postman:test

if ($LASTEXITCODE -ne 0) {
    Fail-Step "Postman/Newman API tests failed"
}

Write-Step "Local smoke validation completed successfully"

Write-Host ""
Write-Host "SUCCESS: Docker stack, API health, synthetic patient API, Pytest, and Newman checks passed." -ForegroundColor Green