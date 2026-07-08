-- validate_idempotency_keys.sql
-- Purpose:
-- Validate idempotency key behavior for retry-safe request handling.
-- This script runs inside a transaction and rolls back all test data.

BEGIN;

CREATE TEMP TABLE idempotency_validation_results (
    validation_order INTEGER NOT NULL,
    validation_step TEXT NOT NULL,
    idempotency_key TEXT NOT NULL,
    request_hash TEXT NOT NULL,
    response_body JSONB NOT NULL,
    replayed_count INTEGER NOT NULL,
    outcome TEXT NOT NULL
) ON COMMIT DROP;


-- First request:
-- The key does not exist yet, so the response is stored.
WITH first_attempt AS (
    INSERT INTO idempotency_keys (
        idempotency_key,
        request_method,
        request_path,
        request_hash,
        response_status,
        response_body,
        trace_id,
        span_id,
        request_id,
        service_name
    )
    VALUES (
        'idem-validation-key-001',
        'POST',
        '/qa/idempotency-validation',
        'sha256:synthetic-request-v1',
        201,
        '{"encounter_id": 9100, "status": "created", "replayed": false}'::jsonb,
        '11111111111111111111111111111111',
        '2222222222222222',
        'idempotency-validation-request',
        'sdet-reliability-api'
    )
    ON CONFLICT (idempotency_key)
    DO UPDATE SET
        replayed_count = idempotency_keys.replayed_count + 1,
        last_replayed_at = NOW()
    WHERE idempotency_keys.request_method = EXCLUDED.request_method
      AND idempotency_keys.request_path = EXCLUDED.request_path
      AND idempotency_keys.request_hash = EXCLUDED.request_hash
    RETURNING
        idempotency_key,
        request_hash,
        response_body,
        replayed_count,
        CASE
            WHEN replayed_count = 0 THEN 'created'
            ELSE 'replayed'
        END AS outcome
)
INSERT INTO idempotency_validation_results (
    validation_order,
    validation_step,
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    outcome
)
SELECT
    1,
    'first_attempt',
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    outcome
FROM first_attempt;


-- Retry with the same key and same request hash:
-- This should not create a new business result.
-- It should reuse the existing stored response and increment replayed_count.
WITH retry_same_request AS (
    INSERT INTO idempotency_keys (
        idempotency_key,
        request_method,
        request_path,
        request_hash,
        response_status,
        response_body,
        trace_id,
        span_id,
        request_id,
        service_name
    )
    VALUES (
        'idem-validation-key-001',
        'POST',
        '/qa/idempotency-validation',
        'sha256:synthetic-request-v1',
        201,
        '{"encounter_id": 9999, "status": "should_not_replace_original", "replayed": true}'::jsonb,
        '11111111111111111111111111111111',
        '3333333333333333',
        'idempotency-validation-retry',
        'sdet-reliability-api'
    )
    ON CONFLICT (idempotency_key)
    DO UPDATE SET
        replayed_count = idempotency_keys.replayed_count + 1,
        last_replayed_at = NOW()
    WHERE idempotency_keys.request_method = EXCLUDED.request_method
      AND idempotency_keys.request_path = EXCLUDED.request_path
      AND idempotency_keys.request_hash = EXCLUDED.request_hash
    RETURNING
        idempotency_key,
        request_hash,
        response_body,
        replayed_count,
        'replayed' AS outcome
)
INSERT INTO idempotency_validation_results (
    validation_order,
    validation_step,
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    outcome
)
SELECT
    2,
    'retry_same_request',
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    outcome
FROM retry_same_request;


-- Retry with the same key but different request hash:
-- This should be treated as a conflict.
-- Same idempotency key should not be reused for a different request payload.
WITH conflicting_reuse AS (
    INSERT INTO idempotency_keys (
        idempotency_key,
        request_method,
        request_path,
        request_hash,
        response_status,
        response_body,
        trace_id,
        span_id,
        request_id,
        service_name
    )
    VALUES (
        'idem-validation-key-001',
        'POST',
        '/qa/idempotency-validation',
        'sha256:different-request-v2',
        201,
        '{"encounter_id": 9998, "status": "conflicting_payload"}'::jsonb,
        '11111111111111111111111111111111',
        '4444444444444444',
        'idempotency-validation-conflict',
        'sdet-reliability-api'
    )
    ON CONFLICT (idempotency_key)
    DO UPDATE SET
        replayed_count = idempotency_keys.replayed_count
    WHERE idempotency_keys.request_method = EXCLUDED.request_method
      AND idempotency_keys.request_path = EXCLUDED.request_path
      AND idempotency_keys.request_hash = EXCLUDED.request_hash
    RETURNING
        idempotency_key,
        request_hash,
        response_body,
        replayed_count,
        'unexpected_replay' AS outcome
)
INSERT INTO idempotency_validation_results (
    validation_order,
    validation_step,
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    outcome
)
SELECT
    3,
    'conflicting_reuse_unexpected',
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    outcome
FROM conflicting_reuse;


-- If the conflicting request returned no row, record the expected conflict.
INSERT INTO idempotency_validation_results (
    validation_order,
    validation_step,
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    outcome
)
SELECT
    3,
    'conflicting_reuse_detected',
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    'conflict_detected'
FROM idempotency_keys
WHERE idempotency_key = 'idem-validation-key-001'
  AND request_hash <> 'sha256:different-request-v2'
  AND NOT EXISTS (
      SELECT 1
      FROM idempotency_validation_results
      WHERE validation_step = 'conflicting_reuse_unexpected'
  );


SELECT
    validation_order,
    validation_step,
    idempotency_key,
    request_hash,
    response_body,
    replayed_count,
    outcome
FROM idempotency_validation_results
ORDER BY validation_order;


ROLLBACK;