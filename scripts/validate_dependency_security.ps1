param(
    [switch]$SkipAdvisoryNodeAudit
)

$ErrorActionPreference = "Stop"

function Write-Section {
    param([string]$Message)

    Write-Host ""
    Write-Host "============================================================"
    Write-Host $Message
    Write-Host "============================================================"
}

function Invoke-BlockingCommand {
    param(
        [string]$Name,
        [string]$Command
    )

    Write-Section "BLOCKING CHECK: $Name"
    Write-Host "Command: $Command"
    Write-Host ""

    Invoke-Expression $Command

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "FAILED: $Name"
        Write-Host "This is a blocking dependency security quality gate failure."
        exit 1
    }

    Write-Host ""
    Write-Host "PASSED: $Name"
}

function Invoke-AdvisoryCommand {
    param(
        [string]$Name,
        [string]$Command
    )

    Write-Section "ADVISORY CHECK: $Name"
    Write-Host "Command: $Command"
    Write-Host ""

    Invoke-Expression $Command

    if ($LASTEXITCODE -ne 0) {
        Write-Host ""
        Write-Host "ADVISORY FINDINGS PRESENT: $Name"
        Write-Host "This result is documented for review but does not fail this script."
        Write-Host "Review the output and determine whether a safe remediation path exists."
        return
    }

    Write-Host ""
    Write-Host "PASSED: $Name"
}

Write-Section "Dependency Security Quality Gate"

Write-Host "Purpose:"
Write-Host "Validate dependency health, Python vulnerability status, and Node audit posture."
Write-Host ""
Write-Host "Blocking checks fail the script."
Write-Host "Advisory checks are reviewed and documented but do not automatically fail the script."

if (-not (Test-Path ".\requirements.txt")) {
    Write-Host "FAILED: requirements.txt was not found."
    exit 1
}

if (-not (Test-Path ".\package.json")) {
    Write-Host "FAILED: package.json was not found."
    exit 1
}

Invoke-BlockingCommand `
    -Name "Python package dependency health" `
    -Command "python -m pip check"

Invoke-BlockingCommand `
    -Name "Python vulnerability audit" `
    -Command "python -m pip_audit -r .\requirements.txt"

Invoke-BlockingCommand `
    -Name "Node production/runtime dependency audit" `
    -Command "npm audit --omit=dev --audit-level=high"

if ($SkipAdvisoryNodeAudit) {
    Write-Section "ADVISORY CHECK SKIPPED: Full Node dev-tooling audit"
    Write-Host "The full Node audit was skipped by request."
}
else {
    Invoke-AdvisoryCommand `
        -Name "Full Node dev-tooling audit" `
        -Command "npm audit --audit-level=high"
}

Write-Section "Dependency Security Quality Gate Complete"

Write-Host "Blocking dependency security checks completed successfully."
Write-Host ""
Write-Host "Reminder:"
Write-Host "Full Node audit findings may still exist in development/test tooling."
Write-Host "Known Newman/Postman transitive findings should be reviewed and documented."
Write-Host "Do not run breaking forced fixes without impact analysis."
