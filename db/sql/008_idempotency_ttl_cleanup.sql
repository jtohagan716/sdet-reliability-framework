-- 008_idempotency_ttl_cleanup.sql
-- Purpose:
-- Add lifecycle management for idempotency keys so the table does not grow forever.

ALTER TABLE idempotency_keys
ADD COLUMN IF NOT EXISTS expires_at TIMESTAMPTZ;

UPDATE idempotency_keys
SET expires_at = created_at + INTERVAL '24 hours'
WHERE expires_at IS NULL;

ALTER TABLE idempotency_keys
ALTER COLUMN expires_at SET DEFAULT NOW() + INTERVAL '24 hours';

ALTER TABLE idempotency_keys
ALTER COLUMN expires_at SET NOT NULL;

CREATE INDEX IF NOT EXISTS idx_idempotency_keys_expires_at
ON idempotency_keys (
    expires_at
);