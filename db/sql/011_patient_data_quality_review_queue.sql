CREATE TABLE IF NOT EXISTS patient_data_quality_review_items (
    review_item_id BIGSERIAL PRIMARY KEY,
    review_item_key TEXT NOT NULL UNIQUE,
    review_source TEXT NOT NULL DEFAULT 'stale_message_protection',
    patient_reference TEXT NOT NULL,
    encounter_reference TEXT NOT NULL,
    related_event_id TEXT NOT NULL,
    related_decision_id BIGINT REFERENCES fhir_stale_message_decisions(stale_message_decision_id),
    review_reason TEXT NOT NULL,
    risk_summary TEXT NOT NULL,
    review_priority TEXT NOT NULL CHECK (
        review_priority IN ('low', 'medium', 'high', 'critical')
    ),
    review_status TEXT NOT NULL CHECK (
        review_status IN (
            'pending_review',
            'blessed_correct',
            'flagged_incorrect',
            'needs_reconciliation',
            'closed'
        )
    ),
    assigned_role TEXT NOT NULL,
    assigned_to TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reviewed_at TIMESTAMPTZ,
    reviewed_by TEXT,
    review_outcome TEXT,
    review_notes TEXT,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS patient_data_quality_review_actions (
    review_action_id BIGSERIAL PRIMARY KEY,
    review_item_id BIGINT NOT NULL REFERENCES patient_data_quality_review_items(review_item_id),
    action_type TEXT NOT NULL CHECK (
        action_type IN (
            'created',
            'assigned',
            'blessed_correct',
            'flagged_incorrect',
            'marked_needs_reconciliation',
            'closed',
            'comment_added'
        )
    ),
    action_by TEXT NOT NULL,
    action_role TEXT NOT NULL,
    action_note TEXT NOT NULL,
    action_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE INDEX IF NOT EXISTS idx_patient_data_quality_review_items_patient_reference
ON patient_data_quality_review_items (patient_reference);

CREATE INDEX IF NOT EXISTS idx_patient_data_quality_review_items_encounter_reference
ON patient_data_quality_review_items (encounter_reference);

CREATE INDEX IF NOT EXISTS idx_patient_data_quality_review_items_related_event_id
ON patient_data_quality_review_items (related_event_id);

CREATE INDEX IF NOT EXISTS idx_patient_data_quality_review_items_related_decision_id
ON patient_data_quality_review_items (related_decision_id);

CREATE INDEX IF NOT EXISTS idx_patient_data_quality_review_items_review_status
ON patient_data_quality_review_items (review_status);

CREATE INDEX IF NOT EXISTS idx_patient_data_quality_review_items_review_priority
ON patient_data_quality_review_items (review_priority);

CREATE INDEX IF NOT EXISTS idx_patient_data_quality_review_actions_review_item_id
ON patient_data_quality_review_actions (review_item_id);

CREATE INDEX IF NOT EXISTS idx_patient_data_quality_review_actions_action_type
ON patient_data_quality_review_actions (action_type);