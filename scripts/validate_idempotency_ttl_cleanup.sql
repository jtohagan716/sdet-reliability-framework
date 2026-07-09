-- validate_idempotency_ttl_cleanup.sql
-- Purpose:
-- Validate that expired idempotency rows can be cleaned up while active rows remain.
-- This script runs inside a transaction and rolls back all test data.

BEGIN;

INSERT INTO idempotency_keys (
    idempotency_key,
    request_method,
    request_path,
    request_hash,
    response_status,
    response_body,
    expires_at,
    service_name
)
VALUES
(
    'ttl-validation-expired-key',
    'POST',
    '/qa/idempotency-validation',
    'sha256:expired-validation',
    201,
    '{"status": "created", "synthetic_result_id": "expired"}'::jsonb,
    NOW() - INTERVAL '1 hour',
    'sdet-reliability-api'
),
(
    'ttl-validation-active-key',
    'POST',
    '/qa/idempotency-validation',
    'sha256:active-validation',
    201,
    '{"status": "created", "synthetic_result_id": "active"}'::jsonb,
    NOW() + INTERVAL '24 hours',
    'sdet-reliability-api'
);

SELECT
    'before_cleanup' AS validation_step,
    idempotency_key,
    expires_at
FROM idempotency_keys
WHERE idempotency_key IN (
    'ttl-validation-expired-key',
    'ttl-validation-active-key'
)
ORDER BY idempotency_key;

WITH deleted_rows AS (
    DELETE FROM idempotency_keys
    WHERE expires_at < NOW()
    RETURNING idempotency_key
)
SELECT
    'cleanup_result' AS validation_step,
    COUNT(*) AS deleted_rows
FROM deleted_rows;

SELECT
    'after_cleanup' AS validation_step,
    idempotency_key,
    expires_at
FROM idempotency_keys
WHERE idempotency_key IN (
    'ttl-validation-expired-key',
    'ttl-validation-active-key'
)
ORDER BY idempotency_key;

ROLLBACK;