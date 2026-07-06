$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== API-to-Database Consistency Validation ==="

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

function Get-DatabasePatientSummary {
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
        Write-Host "FAILED: Database query failed for patient_id $PatientId"
        exit 1
    }

    $json = ($result | Out-String).Trim()

    if ([string]::IsNullOrWhiteSpace($json)) {
        return $null
    }

    return $json | ConvertFrom-Json
}

function Compare-PatientSummary {
    param (
        [Parameter(Mandatory = $true)]
        [int]$PatientId
    )

    Write-Host ""
    Write-Host "Comparing API response to database result for patient_id $PatientId..."

    $apiPatient = Invoke-RestMethod "http://127.0.0.1:8000/patients/$PatientId"
    $databasePatient = Get-DatabasePatientSummary -PatientId $PatientId

    if ($null -eq $databasePatient) {
        Write-Host "FAILED: Database did not return patient_id $PatientId"
        exit 1
    }

    Assert-Equals "patient$PatientId.patient_id" $apiPatient.patient_id $databasePatient.patient_id
    Assert-Equals "patient$PatientId.name" $apiPatient.name $databasePatient.name
    Assert-Equals "patient$PatientId.status" $apiPatient.status $databasePatient.status
    Assert-Equals "patient$PatientId.last_visit" $apiPatient.last_visit $databasePatient.last_visit
}

Write-Host ""
Write-Host "Checking required containers..."

Assert-ContainerRunning "sdet-postgres"
Assert-ContainerRunning "sdet-reliability-api"

Write-Host ""
Write-Host "Checking API container database configuration..."

$patientDataSource = (docker exec sdet-reliability-api printenv PATIENT_DATA_SOURCE).Trim()
Assert-Equals "PATIENT_DATA_SOURCE" $patientDataSource "postgres"

Write-Host ""
Write-Host "Checking API health..."

$health = Invoke-RestMethod "http://127.0.0.1:8000/health"
Assert-Equals "health.status" $health.status "UP"

Write-Host ""
Write-Host "Validating API-to-database consistency..."

Compare-PatientSummary -PatientId 1001
Compare-PatientSummary -PatientId 1002
Compare-PatientSummary -PatientId 1003
Compare-PatientSummary -PatientId 1004

Write-Host ""
Write-Host "Validating missing patient consistency..."

$missingDatabasePatient = Get-DatabasePatientSummary -PatientId 9999

if ($null -ne $missingDatabasePatient) {
    Write-Host "FAILED: Database unexpectedly returned patient_id 9999"
    exit 1
}

try {
    Invoke-RestMethod "http://127.0.0.1:8000/patients/9999" | Out-Null
    Write-Host "FAILED: API should return 404 for patient_id 9999"
    exit 1
}
catch {
    $statusCode = $_.Exception.Response.StatusCode.value__
    Assert-Equals "patient9999.status_code" $statusCode 404
}

Write-Host ""
Write-Host "API-to-database consistency validation passed."
exit 0
