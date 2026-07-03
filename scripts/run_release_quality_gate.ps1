param(
    [string]$ReportPath = "reports/release_quality_gate_v0.9.0.md"
)

$ErrorActionPreference = "Continue"
$results = @()
$overallStart = Get-Date

function Invoke-QualityGateStep {
    param(
        [string]$Name,
        [string]$Command
    )

    Write-Host ""
    Write-Host "===== $Name =====" -ForegroundColor Cyan
    Write-Host $Command

    $start = Get-Date

    $process = Start-Process `
        -FilePath "powershell" `
        -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $Command `
        -Wait `
        -PassThru `
        -NoNewWindow

    $end = Get-Date
    $durationSeconds = [math]::Round(($end - $start).TotalSeconds, 2)

    if ($process.ExitCode -eq 0) {
        $status = "PASS"
        Write-Host "PASS: $Name ($durationSeconds sec)" -ForegroundColor Green
    }
    else {
        $status = "FAIL"
        Write-Host "FAIL: $Name ($durationSeconds sec)" -ForegroundColor Red
    }

    $script:results += [PSCustomObject]@{
        Name = $Name
        Command = $Command
        Status = $status
        ExitCode = $process.ExitCode
        DurationSeconds = $durationSeconds
    }
}

function Write-QualityGateReport {
    param(
        [string]$Path,
        [array]$Results,
        [datetime]$StartedAt,
        [datetime]$CompletedAt
    )

    $reportDirectory = Split-Path $Path -Parent

    if ($reportDirectory -and -not (Test-Path $reportDirectory)) {
        New-Item -ItemType Directory -Path $reportDirectory | Out-Null
    }

    $passed = ($Results | Where-Object { $_.Status -eq "PASS" }).Count
    $failed = ($Results | Where-Object { $_.Status -eq "FAIL" }).Count
    $total = $Results.Count
    $elapsedSeconds = [math]::Round(($CompletedAt - $StartedAt).TotalSeconds, 2)
    $generatedUtc = (Get-Date).ToUniversalTime().ToString("o")

    $lines = @(
        "# Release Quality Gate Report",
        "",
        "Generated UTC: ``$generatedUtc``",
        "Total Gates: ``$total``",
        "Passed: ``$passed``",
        "Failed: ``$failed``",
        "Elapsed Seconds: ``$elapsedSeconds``",
        "",
        "## Summary",
        "",
        "| Gate | Status | Exit Code | Duration Seconds |",
        "|---|---|---:|---:|"
    )

    foreach ($result in $Results) {
        $lines += "| $($result.Name) | $($result.Status) | $($result.ExitCode) | $($result.DurationSeconds) |"
    }

    $lines += @(
        "",
        "## Gate Details",
        ""
    )

    foreach ($result in $Results) {
        $lines += "### $($result.Name)"
        $lines += ""
        $lines += "Status: ``$($result.Status)``"
        $lines += ""
        $lines += "Command:"
        $lines += ""
        $lines += "~~~powershell"
        $lines += $result.Command
        $lines += "~~~"
        $lines += ""
    }

    $lines += @(
        "## Interpretation",
        "",
        "This report captures release-readiness evidence for the project.",
        "",
        "A passing quality gate means the selected automated checks completed successfully before release.",
        "",
        "The gate includes syntax checks, regression testing, Application Programming Interface (API) contract testing, user interface and API automation, accessibility smoke validation, performance baseline evidence, lightweight load testing, and Docker-based smoke validation.",
        "",
        "## International Software Testing Qualifications Board (ISTQB) / Certified Tester Foundation Level (CTFL) Connection",
        "",
        "This workflow represents release exit criteria and regression evidence. The software should not be considered ready for release unless the required checks pass.",
        "",
        "## Department of Homeland Security (DHS) / Section 508 Accessibility Connection",
        "",
        "Accessibility smoke validation is included as part of release readiness. This does not claim full Section 508 certification, but it ensures basic accessibility checks are not treated as optional afterthoughts.",
        "",
        "## Reliability Value",
        "",
        "The release quality gate turns individual validation commands into a repeatable evidence workflow. It helps replace ad hoc release judgment with documented, repeatable checks."
    )

    $lines | Set-Content $Path
}

$gateSteps = @(
    @{
        Name = "Python syntax check - FastAPI app"
        Command = "python -m py_compile .\api_service\app.py"
    },
    @{
        Name = "Python syntax check - performance baseline script"
        Command = "python -m py_compile .\scripts\run_performance_baseline.py"
    },
    @{
        Name = "Python syntax check - lightweight load test script"
        Command = "python -m py_compile .\scripts\run_lightweight_load_test.py"
    },
    @{
        Name = "Full Pytest regression suite"
        Command = "python -m pytest"
    },
    @{
        Name = "Start Docker stack"
        Command = "docker compose up -d --build"
    },
    @{
        Name = "Newman API regression"
        Command = "npm run postman:test"
    },
    @{
        Name = "Focused Section 508 accessibility smoke validation"
        Command = "npx playwright test tests/ui/patient_lookup_accessibility.spec.ts"
    },
    @{
        Name = "Full Playwright automation"
        Command = "npx playwright test"
    },
    @{
        Name = "Performance baseline evidence"
        Command = "python .\scripts\run_performance_baseline.py --output reports/performance_baseline_quality_gate_v0.9.0.md"
    },
    @{
        Name = "Lightweight load test evidence"
        Command = "python .\scripts\run_lightweight_load_test.py --output reports/lightweight_load_test_quality_gate_v0.9.0.md"
    },
    @{
        Name = "Local Docker/API smoke validation"
        Command = ".\scripts\local_smoke_validation.ps1"
    }
)

foreach ($step in $gateSteps) {
    Invoke-QualityGateStep -Name $step.Name -Command $step.Command
}

$overallEnd = Get-Date

Write-QualityGateReport `
    -Path $ReportPath `
    -Results $results `
    -StartedAt $overallStart `
    -CompletedAt $overallEnd

Write-Host ""
Write-Host "Release quality gate report written to: $ReportPath" -ForegroundColor Cyan

$failedCount = ($results | Where-Object { $_.Status -eq "FAIL" }).Count

if ($failedCount -gt 0) {
    Write-Host "Release quality gate failed. Failed gates: $failedCount" -ForegroundColor Red
    exit 1
}

Write-Host "Release quality gate completed successfully." -ForegroundColor Green
exit 0

