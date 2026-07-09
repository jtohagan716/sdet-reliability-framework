-- cleanup_expired_idempotency_keys.sql
-- Purpose:
-- Remove expired idempotency records after their retry-safety window has passed.

WITH deleted_rows AS (
    DELETE FROM idempotency_keys
    WHERE expires_at < NOW()
    RETURNING
        idempotency_key,
        request_method,
        request_path,
        created_at,
        expires_at,
        replayed_count
)
SELECT
    COUNT(*) AS deleted_idempotency_rows
FROM deleted_rows;