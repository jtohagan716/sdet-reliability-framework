Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-LastExitCode {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StageName
    )

    if ($LASTEXITCODE -ne 0) {
        Write-Error (
            "LabFlow quality stage '$StageName' failed " +
            "with exit code $LASTEXITCODE."
        )

        exit $LASTEXITCODE
    }
}

Write-Host ""
Write-Host "============================================================"
Write-Host "Running complete LabFlow quality gates"
Write-Host "============================================================"

Write-Host ""
Write-Host "Checking SQLAlchemy and PostgreSQL schema alignment..."

docker compose exec -T api alembic check
Assert-LastExitCode -StageName "Alembic schema drift"

$apiGateScript = Join-Path `
    $PSScriptRoot `
    "run_api_quality_gates.ps1"

& $apiGateScript
Assert-LastExitCode -StageName "API quality gates"

$databaseGateScript = Join-Path `
    $PSScriptRoot `
    "run_database_quality_gates.ps1"

& $databaseGateScript
Assert-LastExitCode -StageName "Database contract quality gate"

Write-Host ""
Write-Host "============================================================"
Write-Host "All LabFlow quality gates passed."
Write-Host "============================================================"