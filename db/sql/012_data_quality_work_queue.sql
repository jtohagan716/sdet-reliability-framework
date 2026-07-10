CREATE TABLE IF NOT EXISTS data_quality_work_queue (
    work_item_id BIGSERIAL PRIMARY KEY,
    work_item_key TEXT NOT NULL UNIQUE,
    queue_name TEXT NOT NULL DEFAULT 'patient_data_quality_review',
    event_type TEXT NOT NULL,
    source_review_item_key TEXT NOT NULL,
    patient_reference TEXT NOT NULL,
    encounter_reference TEXT NOT NULL,
    priority TEXT NOT NULL CHECK (
        priority IN ('low', 'medium', 'high', 'critical')
    ),
    status TEXT NOT NULL CHECK (
        status IN (
            'ready',
            'processing',
            'completed',
            'failed',
            'dead_letter'
        )
    ),
    payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    attempt_count INTEGER NOT NULL DEFAULT 0,
    max_attempts INTEGER NOT NULL DEFAULT 3,
    available_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    locked_at TIMESTAMPTZ,
    locked_by TEXT,
    processed_at TIMESTAMPTZ,
    error_message TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS data_quality_work_queue_history (
    history_id BIGSERIAL PRIMARY KEY,
    work_item_id BIGINT NOT NULL REFERENCES data_quality_work_queue(work_item_id),
    work_item_key TEXT NOT NULL,
    previous_status TEXT,
    new_status TEXT NOT NULL,
    action_type TEXT NOT NULL CHECK (
        action_type IN (
            'created',
            'claimed',
            'completed',
            'failed',
            'retry_scheduled',
            'moved_to_dead_letter',
            'released'
        )
    ),
    action_by TEXT NOT NULL,
    action_note TEXT NOT NULL,
    action_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_status
ON data_quality_work_queue (status);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_priority
ON data_quality_work_queue (priority);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_available_at
ON data_quality_work_queue (available_at);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_source_review_item_key
ON data_quality_work_queue (source_review_item_key);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_patient_reference
ON data_quality_work_queue (patient_reference);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_encounter_reference
ON data_quality_work_queue (encounter_reference);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_claim_order
ON data_quality_work_queue (status, priority, available_at, work_item_id);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_history_work_item_id
ON data_quality_work_queue_history (work_item_id);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_history_work_item_key
ON data_quality_work_queue_history (work_item_key);

CREATE INDEX IF NOT EXISTS idx_data_quality_work_queue_history_action_type
ON data_quality_work_queue_history (action_type);