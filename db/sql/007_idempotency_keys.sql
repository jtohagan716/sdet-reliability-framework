-- 007_idempotency_keys.sql
-- Purpose:
-- Add database support for idempotency and retry-safe request handling.

CREATE TABLE IF NOT EXISTS idempotency_keys (
    idempotency_key TEXT PRIMARY KEY,

    request_method TEXT NOT NULL,
    request_path TEXT NOT NULL,
    request_hash TEXT NOT NULL,

    response_status INTEGER NOT NULL CHECK (
        response_status >= 100
        AND response_status <= 599
    ),
    response_body JSONB NOT NULL,

    replayed_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_replayed_at TIMESTAMPTZ,

    trace_id TEXT,
    span_id TEXT,
    request_id TEXT,
    service_name TEXT
);

CREATE INDEX IF NOT EXISTS idx_idempotency_keys_request_path
ON idempotency_keys (
    request_method,
    request_path
);

CREATE INDEX IF NOT EXISTS idx_idempotency_keys_trace_id
ON idempotency_keys (
    trace_id
);