BEGIN;

\echo 'Cleaning previous work queue validation records if present...'

DELETE FROM data_quality_work_queue_history
WHERE work_item_key = 'dq-work-queue-review-created-001';

DELETE FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-review-created-001';

DELETE FROM patient_data_quality_review_actions
WHERE review_item_id IN (
    SELECT review_item_id
    FROM patient_data_quality_review_items
    WHERE review_item_key = 'dq-review-work-queue-encounter-example-001'
);

DELETE FROM patient_data_quality_review_items
WHERE review_item_key = 'dq-review-work-queue-encounter-example-001';

\echo 'Creating patient data quality review item that needs queue processing...'

INSERT INTO patient_data_quality_review_items (
    review_item_key,
    review_source,
    patient_reference,
    encounter_reference,
    related_event_id,
    review_reason,
    risk_summary,
    review_priority,
    review_status,
    assigned_role,
    assigned_to,
    details
)
VALUES (
    'dq-review-work-queue-encounter-example-001',
    'stale_message_protection',
    'Patient/example-patient-001',
    'Encounter/example-encounter-work-queue-001',
    'encounter-message-001-partial-work-queue',
    'Older partial Encounter message requires downstream reconciliation review processing',
    'Potential silent downgrade from finished complete Encounter state to in-progress partial state',
    'medium',
    'pending_review',
    'Data Quality Expert',
    'synthetic_data_quality_reviewer',
    jsonb_build_object(
        'queue_required', true,
        'queue_reason', 'review_item_created',
        'synthetic_validation', true
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
VALUES (
    :review_review_item_id,
    'created',
    'system',
    'stale_message_protection_logic',
    'Created patient data quality review item that requires queue processing',
    jsonb_build_object(
        'synthetic_validation', true
    )
);

\echo 'Enqueuing durable data quality work item...'

INSERT INTO data_quality_work_queue (
    work_item_key,
    queue_name,
    event_type,
    source_review_item_key,
    patient_reference,
    encounter_reference,
    priority,
    status,
    payload,
    max_attempts
)
VALUES (
    'dq-work-queue-review-created-001',
    'patient_data_quality_review',
    'patient_data_quality_review_created',
    'dq-review-work-queue-encounter-example-001',
    'Patient/example-patient-001',
    'Encounter/example-encounter-work-queue-001',
    'medium',
    'ready',
    jsonb_build_object(
        'review_item_key', 'dq-review-work-queue-encounter-example-001',
        'patient_reference', 'Patient/example-patient-001',
        'encounter_reference', 'Encounter/example-encounter-work-queue-001',
        'requested_worker_action', 'prepare_for_data_quality_review',
        'synthetic_validation', true
    ),
    3
)
RETURNING work_item_id \gset work_

INSERT INTO data_quality_work_queue_history (
    work_item_id,
    work_item_key,
    previous_status,
    new_status,
    action_type,
    action_by,
    action_note,
    details
)
VALUES (
    :work_work_item_id,
    'dq-work-queue-review-created-001',
    NULL,
    'ready',
    'created',
    'system',
    'Created durable work queue item from patient data quality review item',
    jsonb_build_object(
        'source_review_item_key', 'dq-review-work-queue-encounter-example-001'
    )
);

\echo 'Worker claims one ready work item using row-locking pattern...'

WITH claimed AS (
    SELECT work_item_id
    FROM data_quality_work_queue
    WHERE work_item_key = 'dq-work-queue-review-created-001'
      AND status = 'ready'
      AND available_at <= NOW()
    ORDER BY
        CASE priority
            WHEN 'critical' THEN 1
            WHEN 'high' THEN 2
            WHEN 'medium' THEN 3
            WHEN 'low' THEN 4
            ELSE 5
        END,
        available_at,
        work_item_id
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
UPDATE data_quality_work_queue AS queue
SET
    status = 'processing',
    locked_at = NOW(),
    locked_by = 'synthetic_queue_worker_001',
    attempt_count = attempt_count + 1,
    updated_at = NOW()
FROM claimed
WHERE queue.work_item_id = claimed.work_item_id
RETURNING queue.work_item_id, queue.work_item_key \gset claimed_

INSERT INTO data_quality_work_queue_history (
    work_item_id,
    work_item_key,
    previous_status,
    new_status,
    action_type,
    action_by,
    action_note,
    details
)
VALUES (
    :claimed_work_item_id,
    'dq-work-queue-review-created-001',
    'ready',
    'processing',
    'claimed',
    'synthetic_queue_worker_001',
    'Worker claimed ready data quality work item using FOR UPDATE SKIP LOCKED pattern',
    jsonb_build_object(
        'worker_id', 'synthetic_queue_worker_001',
        'claim_pattern', 'FOR UPDATE SKIP LOCKED'
    )
);

\echo 'Attempting duplicate claim of the same work item...'

WITH duplicate_claim AS (
    SELECT work_item_id
    FROM data_quality_work_queue
    WHERE work_item_key = 'dq-work-queue-review-created-001'
      AND status = 'ready'
      AND available_at <= NOW()
    FOR UPDATE SKIP LOCKED
    LIMIT 1
),
duplicate_update AS (
    UPDATE data_quality_work_queue AS queue
    SET
        status = 'processing',
        locked_at = NOW(),
        locked_by = 'synthetic_queue_worker_002',
        attempt_count = attempt_count + 1,
        updated_at = NOW()
    FROM duplicate_claim
    WHERE queue.work_item_id = duplicate_claim.work_item_id
    RETURNING queue.work_item_id
)
SELECT
    CASE
        WHEN COUNT(*) = 0
        THEN 'passed'
        ELSE 'failed'
    END AS duplicate_claim_prevention_assertion
FROM duplicate_update;

\echo 'Worker completes the claimed work item...'

UPDATE data_quality_work_queue
SET
    status = 'completed',
    processed_at = NOW(),
    error_message = NULL,
    updated_at = NOW()
WHERE work_item_id = :claimed_work_item_id
  AND status = 'processing'
RETURNING work_item_id, work_item_key \gset completed_

INSERT INTO data_quality_work_queue_history (
    work_item_id,
    work_item_key,
    previous_status,
    new_status,
    action_type,
    action_by,
    action_note,
    details
)
VALUES (
    :completed_work_item_id,
    'dq-work-queue-review-created-001',
    'processing',
    'completed',
    'completed',
    'synthetic_queue_worker_001',
    'Worker completed data quality work item and preserved processing evidence',
    jsonb_build_object(
        'worker_id', 'synthetic_queue_worker_001',
        'processing_result', 'prepared_for_data_quality_review'
    )
);

\echo 'Current work queue item:'

SELECT
    work_item_key,
    queue_name,
    event_type,
    source_review_item_key,
    patient_reference,
    encounter_reference,
    priority,
    status,
    attempt_count,
    max_attempts,
    locked_by,
    processed_at IS NOT NULL AS processed_at_recorded,
    error_message
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-review-created-001';

\echo 'Work queue history:'

SELECT
    work_item_key,
    previous_status,
    new_status,
    action_type,
    action_by,
    action_note
FROM data_quality_work_queue_history
WHERE work_item_key = 'dq-work-queue-review-created-001'
ORDER BY history_id;

\echo 'Source review item remains unchanged:'

SELECT
    review_item_key,
    patient_reference,
    encounter_reference,
    review_priority,
    review_status,
    assigned_role,
    assigned_to
FROM patient_data_quality_review_items
WHERE review_item_key = 'dq-review-work-queue-encounter-example-001';

\echo 'Expected queue completion assertion:'

SELECT
    CASE
        WHEN status = 'completed'
         AND attempt_count = 1
         AND locked_by = 'synthetic_queue_worker_001'
         AND processed_at IS NOT NULL
        THEN 'passed'
        ELSE 'failed'
    END AS queue_completion_assertion
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-review-created-001';

\echo 'Expected queue history assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 3
         AND COUNT(*) FILTER (WHERE action_type = 'created') = 1
         AND COUNT(*) FILTER (WHERE action_type = 'claimed') = 1
         AND COUNT(*) FILTER (WHERE action_type = 'completed') = 1
        THEN 'passed'
        ELSE 'failed'
    END AS queue_history_assertion
FROM data_quality_work_queue_history
WHERE work_item_key = 'dq-work-queue-review-created-001';

\echo 'Expected review item unchanged assertion:'

SELECT
    CASE
        WHEN review_status = 'pending_review'
         AND review_priority = 'medium'
         AND assigned_role = 'Data Quality Expert'
        THEN 'passed'
        ELSE 'failed'
    END AS review_item_unchanged_assertion
FROM patient_data_quality_review_items
WHERE review_item_key = 'dq-review-work-queue-encounter-example-001';

\echo 'Expected queue linkage assertion:'

SELECT
    CASE
        WHEN source_review_item_key = 'dq-review-work-queue-encounter-example-001'
         AND patient_reference = 'Patient/example-patient-001'
         AND encounter_reference = 'Encounter/example-encounter-work-queue-001'
        THEN 'passed'
        ELSE 'failed'
    END AS queue_linkage_assertion
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-review-created-001';

ROLLBACK;