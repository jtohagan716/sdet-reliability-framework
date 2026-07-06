$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== Patient Lookup Query Plan and Index Validation ==="

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

function Assert-Contains {
    param (
        [Parameter(Mandatory = $true)]
        [string]$Name,

        [Parameter(Mandatory = $true)]
        [string]$Text,

        [Parameter(Mandatory = $true)]
        [string]$ExpectedSubstring
    )

    if ($Text -notlike "*$ExpectedSubstring*") {
        Write-Host "FAILED: $Name did not contain '$ExpectedSubstring'"
        exit 1
    }

    Write-Host "PASSED: $Name contains '$ExpectedSubstring'"
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
Write-Host "Checking patient lookup index exists..."

$indexExists = docker exec sdet-postgres psql `
    -U sdet_user `
    -d sdet_reliability `
    -t `
    -A `
    -c "SELECT COUNT(*) FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'idx_encounters_completed_patient_date';"

$indexExists = ($indexExists | Out-String).Trim()

Assert-Equals "idx_encounters_completed_patient_date exists" $indexExists "1"

Write-Host ""
Write-Host "Checking patient lookup index definition..."

$indexDefinition = docker exec sdet-postgres psql `
    -U sdet_user `
    -d sdet_reliability `
    -t `
    -A `
    -c "SELECT indexdef FROM pg_indexes WHERE schemaname = 'public' AND indexname = 'idx_encounters_completed_patient_date';"

$indexDefinition = ($indexDefinition | Out-String).Trim()

Assert-Contains "index definition" $indexDefinition "encounters"
Assert-Contains "index definition" $indexDefinition "patient_id"
Assert-Contains "index definition" $indexDefinition "encounter_date"
Assert-Contains "index definition" $indexDefinition "completed"

Write-Host ""
Write-Host "Checking patient lookup SQL result..."

$queryResult = docker exec sdet-postgres psql `
    -U sdet_user `
    -d sdet_reliability `
    -t `
    -A `
    -c "SELECT COALESCE(TO_CHAR(MAX(e.encounter_date), 'YYYY-MM-DD'), '') FROM patients p LEFT JOIN encounters e ON p.patient_id = e.patient_id AND e.status = 'completed' WHERE p.patient_id = 1004 GROUP BY p.patient_id;"

$queryResult = ($queryResult | Out-String).Trim()

Assert-Equals "patient1004.latest_completed_visit" $queryResult "2026-04-02"

Write-Host ""
Write-Host "Capturing EXPLAIN plan for patient lookup query..."

$explainPlan = docker exec sdet-postgres psql `
    -U sdet_user `
    -d sdet_reliability `
    -c "EXPLAIN (ANALYZE, BUFFERS) SELECT p.patient_id, p.first_name || ' ' || p.last_name AS name, p.status, COALESCE(TO_CHAR(MAX(e.encounter_date), 'YYYY-MM-DD'), '') AS last_visit FROM patients p LEFT JOIN encounters e ON p.patient_id = e.patient_id AND e.status = 'completed' WHERE p.patient_id = 1004 GROUP BY p.patient_id, p.first_name, p.last_name, p.status;"

$explainPlanText = ($explainPlan | Out-String)

Write-Host $explainPlanText

Assert-Contains "EXPLAIN plan" $explainPlanText "GroupAggregate"
Assert-Contains "EXPLAIN plan" $explainPlanText "patients_pkey"
Assert-Contains "EXPLAIN plan" $explainPlanText "encounters"
Assert-Contains "EXPLAIN plan" $explainPlanText "Execution Time"

Write-Host ""
Write-Host "Patient lookup query plan and index validation passed."
exit 0
