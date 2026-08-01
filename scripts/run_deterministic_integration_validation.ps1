[CmdletBinding()]
param(
    [string]$ValidationProjectName = "sdet-integration-validation",
    [string]$EvidenceRoot = "reports/test-runs",
    [string]$PythonExecutable = "python",
    [switch]$SkipBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

if (Test-Path variable:PSNativeCommandUseErrorActionPreference) {
    $PSNativeCommandUseErrorActionPreference = $false
}

$repositoryRoot = Split-Path -Parent $PSScriptRoot
$defaultProjectName = Split-Path -Leaf $repositoryRoot
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"

if ([System.IO.Path]::IsPathRooted($EvidenceRoot)) {
    $evidenceDirectory = Join-Path `
        $EvidenceRoot `
        "deterministic-integration-$timestamp"
}
else {
    $evidenceDirectory = Join-Path `
        $repositoryRoot `
        "$EvidenceRoot/deterministic-integration-$timestamp"
}

$junitPath = Join-Path $evidenceDirectory "pytest-results.xml"
$stdoutPath = Join-Path $evidenceDirectory "pytest-stdout.txt"
$stderrPath = Join-Path $evidenceDirectory "pytest-stderr.txt"
$serviceStatePath = Join-Path $evidenceDirectory "docker-compose-ps.txt"
$dockerLogsPath = Join-Path $evidenceDirectory "docker-compose-logs.txt"

$previousComposeProjectName = $env:COMPOSE_PROJECT_NAME
$previousPythonPath = $env:PYTHONPATH

$defaultStackWasRunning = $false
$validationStackStarted = $false
$pytestExitCode = $null

New-Item `
    -ItemType Directory `
    -Force `
    -Path $evidenceDirectory |
    Out-Null

Push-Location $repositoryRoot

try {
    Write-Host "`n========== VALIDATION CONFIGURATION =========="
    Write-Host "Default project    : $defaultProjectName"
    Write-Host "Validation project : $ValidationProjectName"
    Write-Host "Evidence directory : $evidenceDirectory"

    Write-Host "`n========== INSPECT DEFAULT STACK =========="

    $defaultContainers = docker compose `
        -p $defaultProjectName `
        ps `
        -q

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to inspect the default Docker Compose stack."
    }

    $defaultContainers = ($defaultContainers | Out-String).Trim()

    if (-not [string]::IsNullOrWhiteSpace($defaultContainers)) {
        $defaultStackWasRunning = $true

        Write-Host "Stopping the developer stack without deleting its volume."

        docker compose `
            -p $defaultProjectName `
            down `
            --remove-orphans

        if ($LASTEXITCODE -ne 0) {
            throw "Unable to stop the developer stack."
        }
    }
    else {
        Write-Host "The developer stack was not running."
    }

    Write-Host "`n========== REMOVE STALE VALIDATION ENVIRONMENT =========="

    docker compose `
        -p $ValidationProjectName `
        down `
        -v `
        --remove-orphans

    Write-Host "`n========== START ISOLATED VALIDATION ENVIRONMENT =========="

    if ($SkipBuild) {
        docker compose `
            -p $ValidationProjectName `
            up `
            -d
    }
    else {
        docker compose `
            -p $ValidationProjectName `
            up `
            -d `
            --build
    }

    if ($LASTEXITCODE -ne 0) {
        throw "Unable to start the isolated validation stack."
    }

    $validationStackStarted = $true
    $env:COMPOSE_PROJECT_NAME = $ValidationProjectName
    $env:PYTHONPATH = $repositoryRoot

    Write-Host "`n========== WAIT FOR POSTGRESQL =========="

    $postgresReady = $false

    for ($attempt = 1; $attempt -le 30; $attempt++) {
        docker compose `
            -p $ValidationProjectName `
            exec `
            -T `
            postgres `
            pg_isready `
            -U sdet_user `
            -d sdet_reliability `
            *> $null

        if ($LASTEXITCODE -eq 0) {
            Write-Host "PostgreSQL ready on attempt $attempt."
            $postgresReady = $true
            break
        }

        Start-Sleep -Seconds 2
    }

    if (-not $postgresReady) {
        throw "PostgreSQL did not become ready."
    }

    Write-Host "`n========== WAIT FOR API =========="

    $apiReady = $false

    for ($attempt = 1; $attempt -le 30; $attempt++) {
        try {
            $response = Invoke-WebRequest `
                -Uri "http://127.0.0.1:8000/health" `
                -UseBasicParsing `
                -TimeoutSec 2

            if ($response.StatusCode -eq 200) {
                Write-Host "API ready on attempt $attempt."
                $apiReady = $true
                break
            }
        }
        catch {
            Write-Host "Waiting for API... attempt $attempt of 30"
        }

        Start-Sleep -Seconds 2
    }

    if (-not $apiReady) {
        throw "The validation API did not become ready."
    }

    Write-Host "`n========== WAIT FOR OBSERVABILITY ENDPOINTS =========="

    $observabilityEndpoints = @(
        @{
            Name = "Prometheus readiness"
            Uri = "http://127.0.0.1:9090/-/ready"
            RequiredConsecutiveSuccesses = 1
        },
        @{
            Name = "Grafana health"
            Uri = "http://127.0.0.1:3000/api/health"
            RequiredConsecutiveSuccesses = 2
        },
        @{
            Name = "Jaeger UI"
            Uri = "http://127.0.0.1:16686/"
            RequiredConsecutiveSuccesses = 1
        },
        @{
            Name = "OpenTelemetry Collector health"
            Uri = "http://127.0.0.1:13133/"
            RequiredConsecutiveSuccesses = 1
        }
    )

    foreach ($endpoint in $observabilityEndpoints) {
        $endpointReady = $false
        $consecutiveSuccesses = 0
        $requiredSuccesses = [int]$endpoint.RequiredConsecutiveSuccesses

        for ($attempt = 1; $attempt -le 45; $attempt++) {
            try {
                $response = Invoke-WebRequest `
                    -Uri $endpoint.Uri `
                    -UseBasicParsing `
                    -TimeoutSec 5

                if ($response.StatusCode -eq 200) {
                    $consecutiveSuccesses++

                    Write-Host (
                        "$($endpoint.Name): successful readiness response " +
                        "$consecutiveSuccesses of $requiredSuccesses."
                    )

                    if ($consecutiveSuccesses -ge $requiredSuccesses) {
                        $endpointReady = $true
                        break
                    }

                    Start-Sleep -Seconds 2
                    continue
                }
            }
            catch {
                Write-Host (
                    "$($endpoint.Name): readiness attempt $attempt of 45 " +
                    "failed: $($_.Exception.Message)"
                )
            }

            $consecutiveSuccesses = 0
            Start-Sleep -Seconds 2
        }

        if (-not $endpointReady) {
            throw "$($endpoint.Name) did not become ready."
        }

        Write-Host "PASSED: $($endpoint.Name)"
    }

    Write-Host "`n========== PREPARE DATABASE CONTRACT =========="

    & "$PSScriptRoot/prepare_integration_test_database.ps1" `
        -ComposeProjectName $ValidationProjectName

    Write-Host "`n========== RUN COMPLETE PYTHON SUITE =========="

    $pytestProcess = Start-Process `
        -FilePath $PythonExecutable `
        -ArgumentList @(
            "-m",
            "pytest",
            "-q",
            "--junitxml=$junitPath"
        ) `
        -WorkingDirectory $repositoryRoot `
        -NoNewWindow `
        -Wait `
        -PassThru `
        -RedirectStandardOutput $stdoutPath `
        -RedirectStandardError $stderrPath

    $pytestExitCode = $pytestProcess.ExitCode

    Get-Content $stdoutPath

    if (
        (Test-Path $stderrPath) -and
        (Get-Item $stderrPath).Length -gt 0
    ) {
        Get-Content $stderrPath
    }

    docker compose `
        -p $ValidationProjectName `
        ps `
        -a |
        Out-File `
            -FilePath $serviceStatePath `
            -Encoding UTF8

    Write-Host "`nPytest exit code: $pytestExitCode"

    if ($pytestExitCode -ne 0) {
        throw "The complete Python suite failed with exit code $pytestExitCode."
    }

    Write-Host "`nDeterministic integration validation passed."
}
catch {
    Write-Host "`nValidation failed: $($_.Exception.Message)"

    try {
        docker compose `
            -p $ValidationProjectName `
            logs `
            --no-color |
            Out-File `
                -FilePath $dockerLogsPath `
                -Encoding UTF8
    }
    catch {
        Write-Host "Unable to capture Docker logs."
    }

    throw
}
finally {
    Write-Host "`n========== CLEAN VALIDATION ENVIRONMENT =========="

    docker compose `
        -p $ValidationProjectName `
        down `
        -v `
        --remove-orphans

    if ([string]::IsNullOrWhiteSpace($previousComposeProjectName)) {
        Remove-Item Env:COMPOSE_PROJECT_NAME `
            -ErrorAction SilentlyContinue
    }
    else {
        $env:COMPOSE_PROJECT_NAME = $previousComposeProjectName
    }

    if ([string]::IsNullOrWhiteSpace($previousPythonPath)) {
        Remove-Item Env:PYTHONPATH `
            -ErrorAction SilentlyContinue
    }
    else {
        $env:PYTHONPATH = $previousPythonPath
    }

    if ($defaultStackWasRunning) {
        Write-Host "`n========== RESTORE DEVELOPER STACK =========="

        docker compose `
            -p $defaultProjectName `
            up `
            -d

        if ($LASTEXITCODE -ne 0) {
            Write-Host "WARNING: The developer stack could not be restarted."
        }
    }

    Pop-Location
}

Write-Host "`nValidation evidence:"
Write-Host $evidenceDirectory

