Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Invoke-TestStage {
    param(
        [Parameter(Mandatory = $true)]
        [string]$StageName,

        [Parameter(Mandatory = $true)]
        [string[]]$PytestArguments
    )

    Write-Host ""
    Write-Host "============================================================"
    Write-Host "Running LabFlow test stage: $StageName"
    Write-Host "============================================================"

    & python -m pytest @PytestArguments

    if ($LASTEXITCODE -ne 0) {
        Write-Error (
            "LabFlow test stage '$StageName' failed " +
            "with exit code $LASTEXITCODE."
        )

        exit $LASTEXITCODE
    }

    Write-Host ""
    Write-Host "LabFlow test stage '$StageName' passed."
}

Invoke-TestStage `
    -StageName "Smoke" `
    -PytestArguments @(
    "automation/tests/api",
    "-m",
    "smoke",
    "-v",
    "--maxfail=1"
)

Invoke-TestStage `
    -StageName "Regression" `
    -PytestArguments @(
    "automation/tests/api",
    "-m",
    "regression",
    "-v"
)

Write-Host ""
Write-Host "============================================================"
Write-Host "All LabFlow API quality gates passed."
Write-Host "============================================================"