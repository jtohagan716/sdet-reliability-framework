BEGIN;

DELETE FROM patient_data_quality_review_actions
WHERE review_item_id IN (
    SELECT review_item_id
    FROM patient_data_quality_review_items
    WHERE review_item_key = 'dq-review-api-encounter-example-001-stale-message'
);

DELETE FROM patient_data_quality_review_items
WHERE review_item_key = 'dq-review-api-encounter-example-001-stale-message';

DELETE FROM fhir_stale_message_decisions
WHERE stale_event_id = 'encounter-message-001-partial-api-review-queue';

DELETE FROM fhir_current_encounter_state
WHERE resource_reference = 'Encounter/example-encounter-api-review-001';

DELETE FROM fhir_message_events
WHERE event_id IN (
    'encounter-message-002-complete-api-review-queue',
    'encounter-message-001-partial-api-review-queue'
);

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
    'encounter-message-002-complete-api-review-queue',
    'synthetic_fhir_fixture',
    'local_fhir_message_event_lab',
    'encounter_state_update',
    'Encounter/example-encounter-api-review-001',
    2,
    1,
    'complete',
    'finished',
    'accepted',
    '2026-07-09T10:05:00-04:00',
    'sha256:synthetic-encounter-message-002-complete-api-review-queue',
    jsonb_build_object(
        'resourceType', 'Encounter',
        'id', 'example-encounter-api-review-001',
        'status', 'finished',
        'subject', jsonb_build_object(
            'reference', 'Patient/example-patient-001'
        )
    ),
    jsonb_build_object(
        'reason', 'newer complete encounter state accepted as current',
        'api_demo_seed', true
    )
)
RETURNING message_event_id \gset accepted_

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
    'Encounter/example-encounter-api-review-001',
    2,
    'finished',
    'complete',
    'encounter-message-002-complete-api-review-queue',
    :accepted_message_event_id,
    'sha256:synthetic-encounter-message-002-complete-api-review-queue',
    jsonb_build_object(
        'resourceType', 'Encounter',
        'id', 'example-encounter-api-review-001',
        'status', 'finished',
        'subject', jsonb_build_object(
            'reference', 'Patient/example-patient-001'
        )
    ),
    jsonb_build_object(
        'state_protection_rule', 'newer valid sequence number remains current',
        'api_demo_seed', true
    )
);

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
    'encounter-message-001-partial-api-review-queue',
    'synthetic_fhir_fixture',
    'local_fhir_message_event_lab',
    'encounter_state_update',
    'Encounter/example-encounter-api-review-001',
    1,
    2,
    'partial',
    'in-progress',
    'stale',
    '2026-07-09T10:06:00-04:00',
    'sha256:synthetic-encounter-message-001-partial-api-review-queue',
    jsonb_build_object(
        'resourceType', 'Encounter',
        'id', 'example-encounter-api-review-001',
        'status', 'in-progress',
        'subject', jsonb_build_object(
            'reference', 'Patient/example-patient-001'
        )
    ),
    jsonb_build_object(
        'reason', 'older partial message arrived after newer complete state',
        'api_demo_seed', true
    )
)
RETURNING message_event_id \gset stale_

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
    'encounter-message-001-partial-api-review-queue',
    :stale_message_event_id,
    'Encounter/example-encounter-api-review-001',
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
        'api_demo_seed', true,
        'review_possible', true
    )
)
RETURNING stale_message_decision_id \gset decision_

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
    reviewed_at,
    reviewed_by,
    review_outcome,
    review_notes,
    details
)
VALUES (
    'dq-review-api-encounter-example-001-stale-message',
    'stale_message_protection',
    'Patient/example-patient-001',
    'Encounter/example-encounter-api-review-001',
    'encounter-message-001-partial-api-review-queue',
    :decision_stale_message_decision_id,
    'Older partial Encounter message attempted to downgrade the protected current Encounter state',
    'Potential silent downgrade from finished complete Encounter state to in-progress partial state',
    'medium',
    'confirmed_correct',
    'Data Quality Expert',
    'synthetic_data_quality_reviewer',
    NOW(),
    'synthetic_data_quality_reviewer',
    'software_decision_correct',
    'Reviewed stale-message decision. Current finished complete Encounter state should remain protected.',
    jsonb_build_object(
        'api_demo_seed', true,
        'review_trigger', 'stale_message_archived'
    )
)
RETURNING review_item_id \gset review_

INSERT INTO patient_data_quality_review_actions (
    review_item_id,
    action_type,
    action_by,
    action_role,
    action_note,
    details
)
VALUES
(
    :review_review_item_id,
    'created',
    'system',
    'stale_message_protection_logic',
    'Created patient data quality review item from archived stale-message decision',
    jsonb_build_object('api_demo_seed', true)
),
(
    :review_review_item_id,
    'confirmed_correct',
    'synthetic_data_quality_reviewer',
    'Data Quality Expert',
    'Confirmed software decision as correct after reviewing current and stale Encounter message evidence',
    jsonb_build_object('api_demo_seed', true)
);

COMMIT;