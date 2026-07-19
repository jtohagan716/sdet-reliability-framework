Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "============================================================"
Write-Host "Running LabFlow database contract quality gate"
Write-Host "============================================================"

& python -m pytest `
    automation/tests/database `
    -m database `
    -v `
    --maxfail=1

if ($LASTEXITCODE -ne 0) {
    Write-Error (
        "LabFlow database contract quality gate failed " +
        "with exit code $LASTEXITCODE."
    )

    exit $LASTEXITCODE
}

Write-Host ""
Write-Host "============================================================"
Write-Host "LabFlow database contract quality gate passed."
Write-Host "============================================================"