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
    'encounter-message-002-complete',
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
    'sha256:synthetic-encounter-message-002-complete',
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

\echo 'Recording protected current Encounter state from newer complete message...'

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
    'encounter-message-002-complete',
    :accepted_message_event_id,
    'sha256:synthetic-encounter-message-002-complete',
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
    'encounter-message-001-partial',
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
    'sha256:synthetic-encounter-message-001-partial',
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
    'encounter-message-001-partial',
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
        'protected_source_event_id', 'encounter-message-002-complete',
        'review_possible', true,
        'correction_possible', true,
        'replay_possible_from_append_only_history', true
    )
);

\echo 'FHIR stale-message event history:'

SELECT
    event_id,
    resource_reference,
    sequence_number,
    arrival_order,
    payload_completeness,
    resource_status,
    processing_status,
    payload_hash
FROM fhir_message_events
WHERE resource_reference = 'Encounter/example-encounter-001'
ORDER BY arrival_order;

\echo 'Protected current Encounter state:'

SELECT
    resource_reference,
    current_sequence_number,
    current_resource_status,
    current_payload_completeness,
    source_event_id,
    current_payload_hash,
    details
FROM fhir_current_encounter_state
WHERE resource_reference = 'Encounter/example-encounter-001';

\echo 'Archived stale-message decision:'

SELECT
    stale_event_id,
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
FROM fhir_stale_message_decisions
WHERE protected_resource_reference = 'Encounter/example-encounter-001';

\echo 'Expected protected state assertion:'

SELECT
    CASE
        WHEN current_sequence_number = 2
         AND current_resource_status = 'finished'
         AND current_payload_completeness = 'complete'
         AND source_event_id = 'encounter-message-002-complete'
        THEN 'passed'
        ELSE 'failed'
    END AS protected_state_assertion
FROM fhir_current_encounter_state
WHERE resource_reference = 'Encounter/example-encounter-001';

\echo 'Expected stale archive assertion:'

SELECT
    CASE
        WHEN stale_event_id = 'encounter-message-001-partial'
         AND stale_sequence_number = 1
         AND current_sequence_number = 2
         AND decision_status = 'stale_archived'
         AND risk_prevented = 'Prevented downgrade from finished complete state to in-progress partial state'
        THEN 'passed'
        ELSE 'failed'
    END AS stale_archive_assertion
FROM fhir_stale_message_decisions
WHERE protected_resource_reference = 'Encounter/example-encounter-001';

\echo 'Expected append-only history assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 2
        THEN 'passed'
        ELSE 'failed'
    END AS append_only_history_assertion
FROM fhir_message_events
WHERE resource_reference = 'Encounter/example-encounter-001';

ROLLBACK;