BEGIN;

\echo 'Recording newer complete Encounter message event...'

INSERT INTO fhir_message_events (
    event_id,
    source_system,
    interface_name,
    message_type,
    resource_reference,
    sequence_number,
    arrival_order,
    payload_completeness,
    resource_status,
    processing_status,
    received_at,
    payload_hash,
    raw_payload,
    details
)
VALUES (
    'encounter-message-002-complete-review-queue',
    'synthetic_fhir_fixture',
    'local_fhir_message_event_lab',
    'encounter_state_update',
    'Encounter/example-encounter-001',
    2,
    1,
    'complete',
    'finished',
    'accepted',
    '2026-07-09T10:05:00-04:00',
    'sha256:synthetic-encounter-message-002-complete-review-queue',
    jsonb_build_object(
        'resourceType', 'Encounter',
        'id', 'example-encounter-001',
        'status', 'finished',
        'subject', jsonb_build_object(
            'reference', 'Patient/example-patient-001'
        ),
        'period', jsonb_build_object(
            'start', '2026-07-09T09:00:00-04:00',
            'end', '2026-07-09T09:30:00-04:00'
        )
    ),
    jsonb_build_object(
        'fixture', 'test_data/fhir/message_events/encounter-message-sequence-002-complete.json',
        'reason', 'newer complete encounter state accepted as current'
    )
)
RETURNING message_event_id \gset accepted_

\echo 'Recording protected current Encounter state...'

INSERT INTO fhir_current_encounter_state (
    resource_reference,
    current_sequence_number,
    current_resource_status,
    current_payload_completeness,
    source_event_id,
    source_message_event_id,
    current_payload_hash,
    current_payload,
    details
)
VALUES (
    'Encounter/example-encounter-001',
    2,
    'finished',
    'complete',
    'encounter-message-002-complete-review-queue',
    :accepted_message_event_id,
    'sha256:synthetic-encounter-message-002-complete-review-queue',
    jsonb_build_object(
        'resourceType', 'Encounter',
        'id', 'example-encounter-001',
        'status', 'finished',
        'subject', jsonb_build_object(
            'reference', 'Patient/example-patient-001'
        ),
        'period', jsonb_build_object(
            'start', '2026-07-09T09:00:00-04:00',
            'end', '2026-07-09T09:30:00-04:00'
        )
    ),
    jsonb_build_object(
        'state_protection_rule', 'newer valid sequence number remains current',
        'accepted_arrival_order', 1,
        'history_model', 'append_only_events_with_current_state_projection'
    )
)
ON CONFLICT (resource_reference)
DO UPDATE SET
    current_sequence_number = EXCLUDED.current_sequence_number,
    current_resource_status = EXCLUDED.current_resource_status,
    current_payload_completeness = EXCLUDED.current_payload_completeness,
    source_event_id = EXCLUDED.source_event_id,
    source_message_event_id = EXCLUDED.source_message_event_id,
    current_payload_hash = EXCLUDED.current_payload_hash,
    current_payload = EXCLUDED.current_payload,
    details = EXCLUDED.details,
    updated_at = NOW();

\echo 'Recording older partial Encounter message event as stale history...'

INSERT INTO fhir_message_events (
    event_id,
    source_system,
    interface_name,
    message_type,
    resource_reference,
    sequence_number,
    arrival_order,
    payload_completeness,
    resource_status,
    processing_status,
    received_at,
    payload_hash,
    raw_payload,
    details
)
VALUES (
    'encounter-message-001-partial-review-queue',
    'synthetic_fhir_fixture',
    'local_fhir_message_event_lab',
    'encounter_state_update',
    'Encounter/example-encounter-001',
    1,
    2,
    'partial',
    'in-progress',
    'stale',
    '2026-07-09T10:06:00-04:00',
    'sha256:synthetic-encounter-message-001-partial-review-queue',
    jsonb_build_object(
        'resourceType', 'Encounter',
        'id', 'example-encounter-001',
        'status', 'in-progress',
        'subject', jsonb_build_object(
            'reference', 'Patient/example-patient-001'
        ),
        'period', jsonb_build_object(
            'start', '2026-07-09T09:00:00-04:00'
        )
    ),
    jsonb_build_object(
        'fixture', 'test_data/fhir/message_events/encounter-message-sequence-001-partial.json',
        'reason', 'older partial message arrived after newer complete state',
        'archived_for_review', true
    )
)
RETURNING message_event_id \gset stale_

\echo 'Recording stale-message protection decision...'

INSERT INTO fhir_stale_message_decisions (
    stale_event_id,
    stale_message_event_id,
    protected_resource_reference,
    stale_sequence_number,
    current_sequence_number,
    stale_resource_status,
    current_resource_status,
    stale_payload_completeness,
    current_payload_completeness,
    decision_status,
    decision_reason,
    risk_prevented,
    details
)
VALUES (
    'encounter-message-001-partial-review-queue',
    :stale_message_event_id,
    'Encounter/example-encounter-001',
    1,
    2,
    'in-progress',
    'finished',
    'partial',
    'complete',
    'stale_archived',
    'Older partial Encounter message archived and rejected to protect newer complete Encounter state',
    'Prevented downgrade from finished complete state to in-progress partial state',
    jsonb_build_object(
        'stale_arrival_order', 2,
        'protected_source_event_id', 'encounter-message-002-complete-review-queue',
        'review_possible', true,
        'correction_possible', true,
        'replay_possible_from_append_only_history', true
    )
)
RETURNING stale_message_decision_id \gset decision_

\echo 'Creating patient data quality review item from stale-message decision...'

INSERT INTO patient_data_quality_review_items (
    review_item_key,
    review_source,
    patient_reference,
    encounter_reference,
    related_event_id,
    related_decision_id,
    review_reason,
    risk_summary,
    review_priority,
    review_status,
    assigned_role,
    assigned_to,
    details
)
VALUES (
    'dq-review-encounter-example-001-stale-message',
    'stale_message_protection',
    'Patient/example-patient-001',
    'Encounter/example-encounter-001',
    'encounter-message-001-partial-review-queue',
    :decision_stale_message_decision_id,
    'Older partial Encounter message attempted to downgrade the protected current Encounter state',
    'Potential silent downgrade from finished complete Encounter state to in-progress partial state',
    'medium',
    'pending_review',
    'Data Quality Expert',
    'synthetic_data_quality_reviewer',
    jsonb_build_object(
        'review_trigger', 'stale_message_archived',
        'software_decision', 'stale_archived',
        'provider_review_required', false,
        'clinical_escalation_possible', true,
        'appointment_context_available', true
    )
)
RETURNING review_item_id \gset review_

\echo 'Recording review item creation action...'

INSERT INTO patient_data_quality_review_actions (
    review_item_id,
    action_type,
    action_by,
    action_role,
    action_note,
    details
)
VALUES (
    :review_review_item_id,
    'created',
    'system',
    'stale_message_protection_logic',
    'Created patient data quality review item from archived stale-message decision',
    jsonb_build_object(
        'source_decision_id', :decision_stale_message_decision_id,
        'source_event_id', 'encounter-message-001-partial-review-queue'
    )
);

\echo 'Data Quality Expert blesses software decision as correct...'

UPDATE patient_data_quality_review_items
SET
    review_status = 'blessed_correct',
    reviewed_at = NOW(),
    reviewed_by = 'synthetic_data_quality_reviewer',
    review_outcome = 'software_decision_correct',
    review_notes = 'Reviewed stale-message decision. Current finished complete Encounter state should remain protected. Older in-progress partial message should remain archived as stale.'
WHERE review_item_id = :review_review_item_id;

INSERT INTO patient_data_quality_review_actions (
    review_item_id,
    action_type,
    action_by,
    action_role,
    action_note,
    details
)
VALUES (
    :review_review_item_id,
    'blessed_correct',
    'synthetic_data_quality_reviewer',
    'Data Quality Expert',
    'Blessed software decision as correct after reviewing current and stale Encounter message evidence',
    jsonb_build_object(
        'review_outcome', 'software_decision_correct',
        'current_state_confirmed', true,
        'stale_message_confirmed', true
    )
);

\echo 'Patient data quality review item:'

SELECT
    review_item_key,
    patient_reference,
    encounter_reference,
    related_event_id,
    review_reason,
    risk_summary,
    review_priority,
    review_status,
    assigned_role,
    reviewed_by,
    review_outcome,
    review_notes
FROM patient_data_quality_review_items
WHERE review_item_id = :review_review_item_id;

\echo 'Patient data quality review action history:'

SELECT
    action_type,
    action_by,
    action_role,
    action_note
FROM patient_data_quality_review_actions
WHERE review_item_id = :review_review_item_id
ORDER BY review_action_id;

\echo 'Protected current Encounter state remains unchanged:'

SELECT
    resource_reference,
    current_sequence_number,
    current_resource_status,
    current_payload_completeness,
    source_event_id
FROM fhir_current_encounter_state
WHERE resource_reference = 'Encounter/example-encounter-001';

\echo 'Original message history remains preserved:'

SELECT
    event_id,
    sequence_number,
    arrival_order,
    resource_status,
    payload_completeness,
    processing_status
FROM fhir_message_events
WHERE event_id IN (
    'encounter-message-002-complete-review-queue',
    'encounter-message-001-partial-review-queue'
)
ORDER BY arrival_order;

\echo 'Expected review item assertion:'

SELECT
    CASE
        WHEN review_status = 'blessed_correct'
         AND review_outcome = 'software_decision_correct'
         AND assigned_role = 'Data Quality Expert'
        THEN 'passed'
        ELSE 'failed'
    END AS review_item_assertion
FROM patient_data_quality_review_items
WHERE review_item_id = :review_review_item_id;

\echo 'Expected review action history assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 2
        THEN 'passed'
        ELSE 'failed'
    END AS review_action_history_assertion
FROM patient_data_quality_review_actions
WHERE review_item_id = :review_review_item_id;

\echo 'Expected protected current state assertion:'

SELECT
    CASE
        WHEN current_sequence_number = 2
         AND current_resource_status = 'finished'
         AND current_payload_completeness = 'complete'
        THEN 'passed'
        ELSE 'failed'
    END AS protected_current_state_assertion
FROM fhir_current_encounter_state
WHERE resource_reference = 'Encounter/example-encounter-001';

\echo 'Expected original message history assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 2
        THEN 'passed'
        ELSE 'failed'
    END AS original_message_history_assertion
FROM fhir_message_events
WHERE event_id IN (
    'encounter-message-002-complete-review-queue',
    'encounter-message-001-partial-review-queue'
);

ROLLBACK;