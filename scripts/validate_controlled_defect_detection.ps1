$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== Controlled Defect Detection Validation ==="

$overrideFile = Join-Path $env:TEMP "sdet-controlled-defect.override.yml"

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
        throw "$Name mismatch"
    }

    Write-Host "PASSED: $Name = $Actual"
}

function Assert-NotEquals {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [object]$Actual,

        [Parameter(Mandatory = $true)]
        [object]$Unexpected
    )

    if ($Actual -eq $Unexpected) {
        Write-Host "FAILED: $Name should not equal '$Unexpected'"
        throw "$Name unexpectedly matched"
    }

    Write-Host "PASSED: $Name correctly differed. actual='$Actual' unexpected='$Unexpected'"
}

function Wait-ApiHealthy {
    param (
        [int]$Attempts = 30,
        [int]$SleepSeconds = 2
    )

    Write-Host ""
    Write-Host "Waiting for API health endpoint..."

    for ($i = 1; $i -le $Attempts; $i++) {
        try {
            $health = Invoke-RestMethod "http://127.0.0.1:8000/health" -TimeoutSec 3

            if ($health.status -eq "UP") {
                Write-Host "PASSED: API health endpoint is UP"
                return
            }
        }
        catch {
            Write-Host "API not ready yet. Attempt $i of $Attempts..."
            Start-Sleep -Seconds $SleepSeconds
        }
    }

    throw "API health endpoint did not become ready"
}

function Invoke-CommandChecked {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Description,

        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host $Description

    & $Command

    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE"
    }

    Write-Host "PASSED: $Description"
}

function Get-ApiDefectMode {
    return (docker exec sdet-reliability-api printenv PATIENT_LOOKUP_DEFECT_MODE).Trim()
}

function Get-CorrectDatabasePatientSummary {
    param (
        [Parameter(Mandatory = $true)]
        [int]$PatientId
    )

    $sql = @"
SELECT json_build_object(
    'patient_id', p.patient_id,
    'name', p.first_name || ' ' || p.last_name,
    'status', p.status,
    'last_visit', COALESCE(TO_CHAR(MAX(e.encounter_date), 'YYYY-MM-DD'), '')
)::text
FROM patients p
LEFT JOIN encounters e
    ON p.patient_id = e.patient_id
   AND e.status = 'completed'
WHERE p.patient_id = $PatientId
GROUP BY
    p.patient_id,
    p.first_name,
    p.last_name,
    p.status;
"@

    $result = docker exec sdet-postgres psql `
        -U sdet_user `
        -d sdet_reliability `
        -t `
        -A `
        -c $sql

    if ($LASTEXITCODE -ne 0) {
        throw "Database query failed for patient_id $PatientId"
    }

    $json = ($result | Out-String).Trim()

    if ([string]::IsNullOrWhiteSpace($json)) {
        return $null
    }

    return $json | ConvertFrom-Json
}

function Invoke-ApiDatabaseConsistencyValidation {
    param (
        [Parameter(Mandatory = $true)]
        [int]$ExpectedExitCode,

        [Parameter(Mandatory = $true)]
        [string]$Description
    )

    Write-Host ""
    Write-Host $Description

    $process = Start-Process `
        -FilePath "powershell.exe" `
        -ArgumentList @(
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            ".\scripts\validate_api_database_consistency.ps1"
        ) `
        -Wait `
        -PassThru `
        -NoNewWindow

    $actualExitCode = $process.ExitCode

    if ($actualExitCode -ne $ExpectedExitCode) {
        Write-Host "FAILED: Expected exit code $ExpectedExitCode but found $actualExitCode"
        throw "API-to-database consistency validation did not return expected exit code"
    }

    Write-Host "PASSED: API-to-database consistency validation returned expected exit code $actualExitCode"
}

function Restore-NormalDefectMode {
    Write-Host ""
    Write-Host "Restoring normal patient lookup behavior..."

    docker compose up -d --build --force-recreate api

    if ($LASTEXITCODE -ne 0) {
        throw "Failed to restore normal patient lookup behavior"
    }

    Wait-ApiHealthy

    $defectMode = Get-ApiDefectMode
    Assert-Equals "PATIENT_LOOKUP_DEFECT_MODE" $defectMode "none"
}

$scriptCompleted = $false

try {
    Invoke-CommandChecked "Starting normal Docker Compose stack" {
        docker compose up -d --build
    }

    Wait-ApiHealthy

    $normalMode = Get-ApiDefectMode
    Assert-Equals "PATIENT_LOOKUP_DEFECT_MODE" $normalMode "none"

    Invoke-ApiDatabaseConsistencyValidation `
        -ExpectedExitCode 0 `
        -Description "Confirming normal API-to-database consistency validation passes"

    $overrideContent = @"
services:
  api:
    environment:
      PATIENT_LOOKUP_DEFECT_MODE: include_scheduled_last_visit
"@

    Set-Content -Path $overrideFile -Value $overrideContent -Encoding UTF8

    Invoke-CommandChecked "Enabling controlled defect mode" {
        docker compose -f docker-compose.yml -f $overrideFile up -d --build --force-recreate api
    }

    Wait-ApiHealthy

    $defectMode = Get-ApiDefectMode
    Assert-Equals "PATIENT_LOOKUP_DEFECT_MODE" $defectMode "include_scheduled_last_visit"

    Write-Host ""
    Write-Host "Checking that controlled defect changes patient 1004 last_visit..."

    $apiPatient = Invoke-RestMethod "http://127.0.0.1:8000/patients/1004"
    $databasePatient = Get-CorrectDatabasePatientSummary -PatientId 1004

    if ($null -eq $databasePatient) {
        throw "Database did not return patient_id 1004"
    }

    Write-Host "API patient1004.last_visit      = $($apiPatient.last_visit)"
    Write-Host "Correct database last_visit     = $($databasePatient.last_visit)"

    Assert-NotEquals `
        -Name "patient1004.last_visit controlled defect" `
        -Actual $apiPatient.last_visit `
        -Unexpected $databasePatient.last_visit

    Invoke-ApiDatabaseConsistencyValidation `
        -ExpectedExitCode 1 `
        -Description "Confirming API-to-database consistency validation fails when controlled defect is enabled"

    Restore-NormalDefectMode

    Invoke-ApiDatabaseConsistencyValidation `
        -ExpectedExitCode 0 `
        -Description "Confirming API-to-database consistency validation passes after defect mode is disabled"

    $scriptCompleted = $true

    Write-Host ""
    Write-Host "Controlled defect detection validation passed."
}
finally {
    if (Test-Path $overrideFile) {
        Remove-Item $overrideFile -Force
    }

    if (-not $scriptCompleted) {
        Write-Host ""
        Write-Host "Validation did not complete cleanly. Attempting to restore normal behavior..."
        docker compose up -d --build --force-recreate api | Out-Host
    }
}

if (-not $scriptCompleted) {
    exit 1
}

exit 0
