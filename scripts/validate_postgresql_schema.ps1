$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== PostgreSQL Schema Validation ==="

function Invoke-PostgresScalar {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Sql
    )

    $result = docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -t -A -c $Sql

    if ($LASTEXITCODE -ne 0) {
        Write-Host "PostgreSQL command failed."
        exit 1
    }

    return $result.Trim()
}

function Assert-Equals {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Actual,

        [Parameter(Mandatory = $true)]
        [string]$Expected
    )

    if ($Actual -ne $Expected) {
        Write-Host "FAILED: $Name expected $Expected but found $Actual"
        exit 1
    }

    Write-Host "PASSED: $Name = $Actual"
}

Write-Host ""
Write-Host "Checking Docker container status..."

$containerStatus = docker inspect -f "{{.State.Status}}" sdet-postgres 2>$null

if ($LASTEXITCODE -ne 0 -or $containerStatus -ne "running") {
    Write-Host "FAILED: sdet-postgres container is not running."
    Write-Host "Start it with: docker compose up -d postgres"
    exit 1
}

Write-Host "PASSED: sdet-postgres container is running"

Write-Host ""
Write-Host "Validating table counts..."

$patientCount = Invoke-PostgresScalar "SELECT COUNT(*) FROM patients;"
$encounterCount = Invoke-PostgresScalar "SELECT COUNT(*) FROM encounters;"
$encounterDiagnosisCount = Invoke-PostgresScalar "SELECT COUNT(*) FROM encounter_diagnoses;"
$tableCount = Invoke-PostgresScalar "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public' AND table_type = 'BASE TABLE';"

Assert-Equals "table_count" $tableCount "8"
Assert-Equals "patient_count" $patientCount "4"
Assert-Equals "encounter_count" $encounterCount "5"
Assert-Equals "encounter_diagnosis_count" $encounterDiagnosisCount "5"

Write-Host ""
Write-Host "Validating relational joins..."

$manyToManyJoinCount = Invoke-PostgresScalar "SELECT COUNT(*) FROM patients p JOIN encounters e ON p.patient_id = e.patient_id JOIN encounter_diagnoses ed ON e.encounter_id = ed.encounter_id JOIN diagnoses d ON ed.diagnosis_code = d.diagnosis_code;"

Assert-Equals "many_to_many_join_count" $manyToManyJoinCount "5"

$leftJoinRowCount = Invoke-PostgresScalar "SELECT COUNT(*) FROM patients p LEFT JOIN encounters e ON p.patient_id = e.patient_id;"

Assert-Equals "left_join_row_count" $leftJoinRowCount "6"

Write-Host ""
Write-Host "Running sample many-to-many join output..."

docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -c "SELECT p.patient_id, p.first_name, p.last_name, e.encounter_id, d.diagnosis_code, d.diagnosis_name FROM patients p JOIN encounters e ON p.patient_id = e.patient_id JOIN encounter_diagnoses ed ON e.encounter_id = ed.encounter_id JOIN diagnoses d ON ed.diagnosis_code = d.diagnosis_code ORDER BY p.patient_id, e.encounter_id, d.diagnosis_code;"

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: sample join query failed."
    exit 1
}

Write-Host ""
Write-Host "PostgreSQL schema validation passed."
exit 0
