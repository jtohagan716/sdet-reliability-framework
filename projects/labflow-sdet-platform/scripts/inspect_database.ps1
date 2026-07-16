$ErrorActionPreference = "Stop"

docker compose exec postgres `
    psql -U labflow_app -d labflow `
    -c "SELECT id, placer_order_number, synthetic_patient_id, test_code, priority, status, ordered_at, created_at FROM lab_orders ORDER BY created_at DESC LIMIT 20;"
