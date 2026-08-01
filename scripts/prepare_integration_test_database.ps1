[CmdletBinding()]
param(
    [string]$ComposeProjectName = $env:COMPOSE_PROJECT_NAME
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$postgresService = "postgres"
$databaseUser = "sdet_user"
$databaseName = "sdet_reliability"

if ([string]::IsNullOrWhiteSpace($ComposeProjectName)) {
    $ComposeProjectName = Split-Path -Leaf $repositoryRoot
}

$schemaFiles = @(
    "db/sql/004_encounter_audit_logic.sql",
    "db/sql/007_idempotency_keys.sql",
    "db/sql/008_idempotency_ttl_cleanup.sql",
    "db/sql/009_fhir_reference_validation_evidence.sql",
    "db/sql/010_fhir_stale_message_evidence.sql",
    "db/sql/011_patient_data_quality_review_queue.sql",
    "db/sql/012_data_quality_work_queue.sql"
)

$requiredRelations = @(
    "encounter_audit",
    "idempotency_keys",
    "fhir_validation_runs",
    "fhir_resource_checks",
    "fhir_reference_checks",
    "fhir_message_events",
    "fhir_current_encounter_state",
    "fhir_stale_message_decisions",
    "patient_data_quality_review_items",
    "patient_data_quality_review_actions",
    "data_quality_work_queue",
    "data_quality_work_queue_history"
)

Push-Location $repositoryRoot

try {
    Write-Host "`n========== VERIFY POSTGRESQL =========="
    Write-Host "Compose project: $ComposeProjectName"

    $containerId = docker compose `
        -p $ComposeProjectName `
        ps `
        -q `
        $postgresService

    $containerExitCode = $LASTEXITCODE
    $containerId = ($containerId | Out-String).Trim()

    if (
        $containerExitCode -ne 0 -or
        [string]::IsNullOrWhiteSpace($containerId)
    ) {
        throw "PostgreSQL Docker service is not running."
    }

    docker compose `
        -p $ComposeProjectName `
        exec `
        -T `
        $postgresService `
        pg_isready `
        -U $databaseUser `
        -d $databaseName

    if ($LASTEXITCODE -ne 0) {
        throw "PostgreSQL is running but not ready."
    }

    Write-Host "`n========== VERIFY BASE DATABASE =========="

    foreach ($baseRelation in @("patients", "encounters")) {
        $resolved = docker compose `
            -p $ComposeProjectName `
            exec `
            -T `
            $postgresService `
            psql `
            -X `
            -A `
            -t `
            -U $databaseUser `
            -d $databaseName `
            -v ON_ERROR_STOP=1 `
            -c "SELECT to_regclass('public.$baseRelation');"

        $queryExitCode = $LASTEXITCODE
        $resolved = ($resolved | Out-String).Trim()

        if (
            $queryExitCode -ne 0 -or
            [string]::IsNullOrWhiteSpace($resolved)
        ) {
            throw "Base relation is unavailable: $baseRelation"
        }

        Write-Host "PASSED: $baseRelation"
    }

    Write-Host "`n========== APPLY REQUIRED SCHEMAS =========="

    foreach ($relativePath in $schemaFiles) {
        $schemaPath = Join-Path $repositoryRoot $relativePath

        if (-not (Test-Path $schemaPath -PathType Leaf)) {
            throw "Schema file not found: $relativePath"
        }

        Write-Host "Applying: $relativePath"

        Get-Content $schemaPath -Raw |
            docker compose `
                -p $ComposeProjectName `
                exec `
                -T `
                $postgresService `
                psql `
                -X `
                -U $databaseUser `
                -d $databaseName `
                -v ON_ERROR_STOP=1

        $schemaExitCode = $LASTEXITCODE

        if ($schemaExitCode -ne 0) {
            throw (
                "Schema application failed with exit code " +
                "${schemaExitCode}: $relativePath"
            )
        }

        Write-Host "PASSED: $relativePath"
    }

    Write-Host "`n========== VERIFY REQUIRED TABLES =========="

    foreach ($relation in $requiredRelations) {
        $resolved = docker compose `
            -p $ComposeProjectName `
            exec `
            -T `
            $postgresService `
            psql `
            -X `
            -A `
            -t `
            -U $databaseUser `
            -d $databaseName `
            -v ON_ERROR_STOP=1 `
            -c "SELECT to_regclass('public.$relation');"

        $queryExitCode = $LASTEXITCODE
        $resolved = ($resolved | Out-String).Trim()

        if (
            $queryExitCode -ne 0 -or
            [string]::IsNullOrWhiteSpace($resolved)
        ) {
            throw "Required table was not provisioned: $relation"
        }

        Write-Host "PASSED: $relation"
    }

    Write-Host "`n========== VERIFY AUDIT TRIGGER =========="

    $triggerCount = docker compose `
        -p $ComposeProjectName `
        exec `
        -T `
        $postgresService `
        psql `
        -X `
        -A `
        -t `
        -U $databaseUser `
        -d $databaseName `
        -v ON_ERROR_STOP=1 `
        -c "SELECT COUNT(*) FROM pg_trigger WHERE tgname = 'trg_audit_encounter_changes' AND NOT tgisinternal;"

    $triggerExitCode = $LASTEXITCODE
    $triggerCount = ($triggerCount | Out-String).Trim()

    if (
        $triggerExitCode -ne 0 -or
        $triggerCount -ne "1"
    ) {
        throw "Encounter audit trigger was not provisioned."
    }

    Write-Host "PASSED: trg_audit_encounter_changes"
    Write-Host "`nIntegration-test database preparation passed."
}
finally {
    Pop-Location
}
