param(
    [string]$PlacerOrderNumber = "ORD-1001",
    [string]$SyntheticPatientId = "SYN-PAT-1001",
    [string]$TestCode = "CBC",
    [ValidateSet("ROUTINE", "STAT")]
    [string]$Priority = "ROUTINE"
)

$ErrorActionPreference = "Stop"

$body = @{
    placer_order_number = $PlacerOrderNumber
    synthetic_patient_id = $SyntheticPatientId
    test_code = $TestCode
    priority = $Priority
    ordered_at = (Get-Date).ToString("o")
} | ConvertTo-Json

Invoke-RestMethod `
    -Method Post `
    -Uri http://localhost:8000/api/v1/lab-orders `
    -ContentType "application/json" `
    -Body $body
