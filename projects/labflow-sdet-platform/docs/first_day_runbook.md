# First-Day Runbook

## Goal

Install, configure, start, and inspect LabFlow v0.1 without writing application
code.

## Prepare configuration

```powershell
Copy-Item .env.example .env
notepad .env
```

## Build and start

```powershell
docker compose up --build -d
```

## Verify containers

```powershell
docker compose ps
```

Expected:

- `labflow-postgres` healthy
- `labflow-api` healthy

## Inspect logs

```powershell
docker compose logs --tail 100 postgres
docker compose logs --tail 100 api
```

## Verify health

```powershell
Invoke-RestMethod http://localhost:8000/health/live
Invoke-RestMethod http://localhost:8000/health/ready
```

## Create a synthetic order

```powershell
$body = @{
    placer_order_number = "ORD-1001"
    synthetic_patient_id = "SYN-PAT-1001"
    test_code = "CBC"
    priority = "ROUTINE"
    ordered_at = "2026-07-14T10:00:00-04:00"
} | ConvertTo-Json

$order = Invoke-RestMethod `
    -Method Post `
    -Uri http://localhost:8000/api/v1/lab-orders `
    -ContentType "application/json" `
    -Body $body

$order
```

## Retrieve it

```powershell
Invoke-RestMethod `
    -Uri "http://localhost:8000/api/v1/lab-orders/$($order.id)"
```

## Inspect PostgreSQL

```powershell
docker compose exec postgres psql -U labflow_app -d labflow
```

Then:

```sql
\d lab_orders
SELECT * FROM lab_orders;
```

Exit with `\q`.

## Stop

```powershell
docker compose down
```

Delete all local database data only when intentional:

```powershell
docker compose down -v
```
