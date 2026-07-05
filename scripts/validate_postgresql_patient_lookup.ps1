$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== PostgreSQL-Backed Patient Lookup Validation ==="

function Assert-Equals {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [object]$Actual,

        [Parameter(Mandatory = $true)]
        [object]$Expected
    )

    if ($Actual -ne $Expected) {
        Write-Host "FAILED: $Name expected '$Expected' but found '$Actual'"
        exit 1
    }

    Write-Host "PASSED: $Name = $Actual"
}

function Assert-ContainerRunning {
    param (
        [Parameter(Mandatory = $true)]
        [string]$ContainerName
    )

    $containerStatus = docker inspect -f "{{.State.Status}}" $ContainerName 2>$null

    if ($LASTEXITCODE -ne 0 -or $containerStatus -ne "running") {
        Write-Host "FAILED: $ContainerName container is not running."
        Write-Host "Start the stack with: docker compose up -d --build"
        exit 1
    }

    Write-Host "PASSED: $ContainerName container is running"
}

Write-Host ""
Write-Host "Checking required containers..."

Assert-ContainerRunning "sdet-postgres"
Assert-ContainerRunning "sdet-reliability-api"

Write-Host ""
Write-Host "Checking API container database configuration..."

$patientDataSource = (docker exec sdet-reliability-api printenv PATIENT_DATA_SOURCE).Trim()
$databaseUrl = (docker exec sdet-reliability-api printenv DATABASE_URL).Trim()

Assert-Equals "PATIENT_DATA_SOURCE" $patientDataSource "postgres"

if ($databaseUrl -notlike "postgresql://sdet_user:*@postgres:5432/sdet_reliability") {
    Write-Host "FAILED: DATABASE_URL does not point to the Docker Compose PostgreSQL service"
    Write-Host "Actual DATABASE_URL: $databaseUrl"
    exit 1
}

Write-Host "PASSED: DATABASE_URL points to PostgreSQL service"

Write-Host ""
Write-Host "Checking API health..."

$health = Invoke-RestMethod "http://127.0.0.1:8000/health"
Assert-Equals "health.status" $health.status "UP"

Write-Host ""
Write-Host "Validating PostgreSQL-backed patient responses..."

$patient1001 = Invoke-RestMethod "http://127.0.0.1:8000/patients/1001"

Assert-Equals "patient1001.patient_id" $patient1001.patient_id 1001
Assert-Equals "patient1001.name" $patient1001.name "Alex Morgan"
Assert-Equals "patient1001.status" $patient1001.status "active"
Assert-Equals "patient1001.last_visit" $patient1001.last_visit "2026-06-15"

$patient1002 = Invoke-RestMethod "http://127.0.0.1:8000/patients/1002"

Assert-Equals "patient1002.patient_id" $patient1002.patient_id 1002
Assert-Equals "patient1002.name" $patient1002.name "Jordan Lee"
Assert-Equals "patient1002.status" $patient1002.status "inactive"
Assert-Equals "patient1002.last_visit" $patient1002.last_visit "2026-05-20"

Write-Host ""
Write-Host "Validating not-found behavior..."

try {
    Invoke-RestMethod "http://127.0.0.1:8000/patients/9999" | Out-Null
    Write-Host "FAILED: /patients/9999 should return 404"
    exit 1
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Assert-Equals "patient9999.status_code" $statusCode 404
}

Write-Host ""
Write-Host "PostgreSQL-backed patient lookup validation passed."
exit 0
