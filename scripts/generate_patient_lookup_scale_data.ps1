param (
    [int]$PatientCount = 1000,
    [int]$EncountersPerPatient = 50,
    [int]$StartingPatientId = 500000,
    [int]$StartingEncounterId = 7000000,
    [switch]$CleanExisting
)

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "=== Patient Lookup Scale Data Generator ==="

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

Assert-ContainerRunning "sdet-postgres"

if ($PatientCount -le 0) {
    Write-Host "FAILED: PatientCount must be greater than 0"
    exit 1
}

if ($EncountersPerPatient -le 0) {
    Write-Host "FAILED: EncountersPerPatient must be greater than 0"
    exit 1
}

$endingPatientId = $StartingPatientId + $PatientCount - 1
$totalEncounters = $PatientCount * $EncountersPerPatient
$endingEncounterId = $StartingEncounterId + $totalEncounters - 1

Write-Host ""
Write-Host "Scale data parameters:"
Write-Host "PatientCount: $PatientCount"
Write-Host "EncountersPerPatient: $EncountersPerPatient"
Write-Host "StartingPatientId: $StartingPatientId"
Write-Host "EndingPatientId: $endingPatientId"
Write-Host "StartingEncounterId: $StartingEncounterId"
Write-Host "EndingEncounterId: $endingEncounterId"
Write-Host "TotalEncounters: $totalEncounters"

Write-Host ""
Write-Host "Checking provider and facility reference data..."

$referenceSql = @"
SELECT
    (SELECT COUNT(*) FROM providers) AS provider_count,
    (SELECT COUNT(*) FROM facilities) AS facility_count;
"@

docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -c $referenceSql

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Unable to inspect provider and facility reference data"
    exit 1
}

if ($CleanExisting) {
    Write-Host ""
    Write-Host "Cleaning existing performance-scale data in configured ID range..."

    $cleanSql = @"
DELETE FROM encounters
WHERE patient_id BETWEEN $StartingPatientId AND $endingPatientId;

DELETE FROM patients
WHERE patient_id BETWEEN $StartingPatientId AND $endingPatientId;
"@

    docker exec -i sdet-postgres psql -U sdet_user -d sdet_reliability -v ON_ERROR_STOP=1 -c $cleanSql

    if ($LASTEXITCODE -ne 0) {
        Write-Host "FAILED: Unable to clean existing performance-scale data"
        exit 1
    }

    Write-Host "PASSED: Existing performance-scale data cleaned"
}

Write-Host ""
Write-Host "Generating synthetic performance patients..."

$patientSql = @"
INSERT INTO patients (
    patient_id,
    first_name,
    last_name,
    date_of_birth,
    status
)
SELECT
    patient_id,
    'PerfFirst' || patient_id::text AS first_name,
    'PerfLast' || patient_id::text AS last_name,
    DATE '1970-01-01' + ((patient_id - $StartingPatientId) % 15000) AS date_of_birth,
    CASE
        WHEN patient_id % 10 = 0 THEN 'inactive'
        ELSE 'active'
    END AS status
FROM generate_series($StartingPatientId, $endingPatientId) AS patient_id
ON CONFLICT (patient_id) DO NOTHING;
"@

docker exec -i sdet-postgres psql -U sdet_user -d sdet_reliability -v ON_ERROR_STOP=1 -c $patientSql

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Unable to generate performance patients"
    exit 1
}

Write-Host "PASSED: Synthetic performance patients generated"

Write-Host ""
Write-Host "Generating synthetic performance encounters..."

$encounterSql = @"
WITH provider_reference AS (
    SELECT array_agg(provider_id ORDER BY provider_id) AS provider_ids
    FROM providers
),
facility_reference AS (
    SELECT array_agg(facility_id ORDER BY facility_id) AS facility_ids
    FROM facilities
)
INSERT INTO encounters (
    encounter_id,
    patient_id,
    provider_id,
    facility_id,
    encounter_date,
    encounter_type,
    status
)
SELECT
    $StartingEncounterId
        + ((patient_id - $StartingPatientId) * $EncountersPerPatient)
        + encounter_number AS encounter_id,
    patient_id,
    provider_reference.provider_ids[
        ((patient_id + encounter_number) % array_length(provider_reference.provider_ids, 1)) + 1
    ] AS provider_id,
    facility_reference.facility_ids[
        ((patient_id + encounter_number) % array_length(facility_reference.facility_ids, 1)) + 1
    ] AS facility_id,
    DATE '2026-01-01' - ((encounter_number % 365) * INTERVAL '1 day') AS encounter_date,
    CASE
        WHEN encounter_number % 3 = 0 THEN 'Primary Care'
        WHEN encounter_number % 3 = 1 THEN 'Specialty'
        ELSE 'Follow-up'
    END AS encounter_type,
    CASE
        WHEN encounter_number % 5 = 0 THEN 'scheduled'
        ELSE 'completed'
    END AS status
FROM generate_series($StartingPatientId, $endingPatientId) AS patient_id
CROSS JOIN generate_series(1, $EncountersPerPatient) AS encounter_number
CROSS JOIN provider_reference
CROSS JOIN facility_reference
ON CONFLICT (encounter_id) DO NOTHING;
"@

docker exec -i sdet-postgres psql -U sdet_user -d sdet_reliability -v ON_ERROR_STOP=1 -c $encounterSql

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Unable to generate performance encounters"
    exit 1
}

Write-Host "PASSED: Synthetic performance encounters generated"

Write-Host ""
Write-Host "Refreshing PostgreSQL statistics..."

docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -v ON_ERROR_STOP=1 -c "ANALYZE patients; ANALYZE encounters;"

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Unable to refresh PostgreSQL statistics"
    exit 1
}

Write-Host "PASSED: PostgreSQL statistics refreshed"

Write-Host ""
Write-Host "Validating generated row counts..."

$countSql = @"
SELECT
    (SELECT COUNT(*) FROM patients WHERE patient_id BETWEEN $StartingPatientId AND $endingPatientId) AS performance_patient_count,
    (SELECT COUNT(*) FROM encounters WHERE patient_id BETWEEN $StartingPatientId AND $endingPatientId) AS performance_encounter_count,
    (SELECT COUNT(*) FROM encounters WHERE patient_id BETWEEN $StartingPatientId AND $endingPatientId AND status = 'completed') AS completed_encounter_count,
    (SELECT COUNT(*) FROM encounters WHERE patient_id BETWEEN $StartingPatientId AND $endingPatientId AND status = 'scheduled') AS scheduled_encounter_count;
"@

docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -c $countSql

if ($LASTEXITCODE -ne 0) {
    Write-Host "FAILED: Unable to validate generated row counts"
    exit 1
}

Write-Host ""
Write-Host "Patient lookup scale data generation completed."
exit 0
