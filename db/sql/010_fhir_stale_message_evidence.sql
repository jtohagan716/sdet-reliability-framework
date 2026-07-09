CREATE TABLE IF NOT EXISTS fhir_message_events (
    message_event_id BIGSERIAL PRIMARY KEY,
    event_id TEXT NOT NULL UNIQUE,
    source_system TEXT NOT NULL DEFAULT 'synthetic_fhir_fixture',
    interface_name TEXT NOT NULL DEFAULT 'local_fhir_message_event_lab',
    message_type TEXT NOT NULL DEFAULT 'encounter_state_update',
    resource_reference TEXT NOT NULL,
    sequence_number INTEGER NOT NULL,
    arrival_order INTEGER NOT NULL,
    payload_completeness TEXT NOT NULL CHECK (
        payload_completeness IN ('partial', 'complete')
    ),
    resource_status TEXT NOT NULL,
    processing_status TEXT NOT NULL CHECK (
        processing_status IN ('accepted', 'stale', 'rejected', 'conflict', 'duplicate')
    ),
    received_at TIMESTAMPTZ NOT NULL,
    processed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    payload_hash TEXT NOT NULL,
    raw_payload JSONB NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fhir_current_encounter_state (
    encounter_state_id BIGSERIAL PRIMARY KEY,
    resource_reference TEXT NOT NULL UNIQUE,
    current_sequence_number INTEGER NOT NULL,
    current_resource_status TEXT NOT NULL,
    current_payload_completeness TEXT NOT NULL CHECK (
        current_payload_completeness IN ('partial', 'complete')
    ),
    source_event_id TEXT NOT NULL,
    source_message_event_id BIGINT REFERENCES fhir_message_events(message_event_id),
    current_payload_hash TEXT NOT NULL,
    current_payload JSONB NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fhir_stale_message_decisions (
    stale_message_decision_id BIGSERIAL PRIMARY KEY,
    stale_event_id TEXT NOT NULL,
    stale_message_event_id BIGINT REFERENCES fhir_message_events(message_event_id),
    protected_resource_reference TEXT NOT NULL,
    stale_sequence_number INTEGER NOT NULL,
    current_sequence_number INTEGER NOT NULL,
    stale_resource_status TEXT NOT NULL,
    current_resource_status TEXT NOT NULL,
    stale_payload_completeness TEXT NOT NULL CHECK (
        stale_payload_completeness IN ('partial', 'complete')
    ),
    current_payload_completeness TEXT NOT NULL CHECK (
        current_payload_completeness IN ('partial', 'complete')
    ),
    decision_status TEXT NOT NULL CHECK (
        decision_status IN ('stale_archived', 'accepted', 'rejected', 'conflict')
    ),
    decision_reason TEXT NOT NULL,
    risk_prevented TEXT NOT NULL,
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    decided_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fhir_message_events_event_id
ON fhir_message_events (event_id);

CREATE INDEX IF NOT EXISTS idx_fhir_message_events_resource_reference
ON fhir_message_events (resource_reference);

CREATE INDEX IF NOT EXISTS idx_fhir_message_events_sequence_number
ON fhir_message_events (sequence_number);

CREATE INDEX IF NOT EXISTS idx_fhir_message_events_processing_status
ON fhir_message_events (processing_status);

CREATE INDEX IF NOT EXISTS idx_fhir_message_events_payload_hash
ON fhir_message_events (payload_hash);

CREATE INDEX IF NOT EXISTS idx_fhir_current_encounter_state_resource_reference
ON fhir_current_encounter_state (resource_reference);

CREATE INDEX IF NOT EXISTS idx_fhir_current_encounter_state_source_event_id
ON fhir_current_encounter_state (source_event_id);

CREATE INDEX IF NOT EXISTS idx_fhir_stale_message_decisions_stale_event_id
ON fhir_stale_message_decisions (stale_event_id);

CREATE INDEX IF NOT EXISTS idx_fhir_stale_message_decisions_resource_reference
ON fhir_stale_message_decisions (protected_resource_reference);

CREATE INDEX IF NOT EXISTS idx_fhir_stale_message_decisions_decision_status
ON fhir_stale_message_decisions (decision_status);