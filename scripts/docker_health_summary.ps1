Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " SDET Reliability Framework - Docker Health Summary" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan

Write-Host ""
Write-Host "1) Docker Compose Services" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

try {
    docker compose ps --format "table {{.Name}}\t{{.Service}}\t{{.State}}\t{{.Status}}"
}
catch {
    Write-Host "Unable to read Docker Compose service status." -ForegroundColor Red
}

Write-Host ""
Write-Host "2) Container Resource Snapshot" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

try {
    docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}"
}
catch {
    Write-Host "Unable to read Docker container resource usage." -ForegroundColor Red
}

Write-Host ""
Write-Host "3) Application Endpoint Checks" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

Write-Host "API /health:" -ForegroundColor White
try {
    $apiHealth = curl.exe -s http://localhost:8000/health
    if ($apiHealth -match '"status":"UP"') {
        Write-Host "API reachable | status UP" -ForegroundColor Green
        Write-Host $apiHealth
    }
    else {
        Write-Host "API responded, but status was not clearly UP" -ForegroundColor DarkYellow
        Write-Host $apiHealth
    }
}
catch {
    Write-Host "API health check failed" -ForegroundColor Red
}

Write-Host ""
Write-Host "4) Observability Endpoint Checks" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

$endpoints = @(
    @{ Name = "Jaeger UI"; Url = "http://localhost:16686" },
    @{ Name = "Prometheus UI"; Url = "http://localhost:9090" },
    @{ Name = "Grafana UI"; Url = "http://localhost:3000" },
    @{ Name = "OpenTelemetry Collector Health"; Url = "http://localhost:13133" }
)

foreach ($endpoint in $endpoints) {
    try {
        $response = Invoke-WebRequest -Uri $endpoint.Url -UseBasicParsing -TimeoutSec 5
        Write-Host "$($endpoint.Name) reachable | HTTP $($response.StatusCode)" -ForegroundColor Green
    }
    catch {
        Write-Host "$($endpoint.Name) not reachable | $($endpoint.Url)" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "5) PostgreSQL Readiness" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

try {
    docker compose exec -T postgres pg_isready -U sdet_user -d sdet_reliability
}
catch {
    Write-Host "PostgreSQL readiness check failed." -ForegroundColor Red
}

Write-Host ""
Write-Host "6) Recent API Logs" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

try {
    docker compose logs api --tail=20
}
catch {
    Write-Host "Unable to read recent API logs." -ForegroundColor Red
}

Write-Host ""
Write-Host "7) Recent PostgreSQL Logs" -ForegroundColor Yellow
Write-Host "------------------------------------------------------------"

try {
    docker compose logs postgres --tail=20
}
catch {
    Write-Host "Unable to read recent PostgreSQL logs." -ForegroundColor Red
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host " Docker Health Summary Complete" -ForegroundColor Cyan
Write-Host "============================================================" -ForegroundColor Cyan
Write-Host ""