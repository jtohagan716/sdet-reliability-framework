SELECT current_database(), current_user, version();

\d+ lab_orders

SELECT COUNT(*) AS order_count
FROM lab_orders;

SELECT
    id,
    placer_order_number,
    synthetic_patient_id,
    test_code,
    priority,
    status,
    ordered_at,
    created_at
FROM lab_orders
ORDER BY created_at DESC
LIMIT 20;

SELECT indexname, indexdef
FROM pg_indexes
WHERE tablename = 'lab_orders'
ORDER BY indexname;

SELECT
    pid,
    usename,
    application_name,
    client_addr,
    state,
    wait_event_type,
    wait_event,
    query_start,
    query
FROM pg_stat_activity
WHERE datname = current_database()
ORDER BY query_start DESC;
