BEGIN;

\echo 'Cleaning previous retry/dead-letter validation records if present...'

DELETE FROM data_quality_work_queue_history
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001';

DELETE FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001';

DELETE FROM patient_data_quality_review_actions
WHERE review_item_id IN (
    SELECT review_item_id
    FROM patient_data_quality_review_items
    WHERE review_item_key = 'dq-review-retry-dead-letter-encounter-example-001'
);

DELETE FROM patient_data_quality_review_items
WHERE review_item_key = 'dq-review-retry-dead-letter-encounter-example-001';

\echo 'Creating patient data quality review item that will produce retryable queue work...'

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
    'dq-review-retry-dead-letter-encounter-example-001',
    'stale_message_protection',
    'Patient/example-patient-001',
    'Encounter/example-encounter-retry-dead-letter-001',
    'encounter-message-001-partial-retry-dead-letter',
    'Older partial Encounter message requires queue processing with retry and dead-letter handling',
    'Potential silent downgrade from finished complete Encounter state to in-progress partial state',
    'high',
    'pending_review',
    'Data Quality Expert',
    'synthetic_data_quality_reviewer',
    jsonb_build_object(
        'queue_required', true,
        'retry_validation', true,
        'synthetic_validation', true
    )
);

INSERT INTO patient_data_quality_review_actions (
    review_item_id,
    action_type,
    action_by,
    action_role,
    action_note,
    details
)
SELECT
    review_item_id,
    'created',
    'system',
    'stale_message_protection_logic',
    'Created patient data quality review item that requires retryable queue processing',
    jsonb_build_object(
        'retry_validation', true,
        'synthetic_validation', true
    )
FROM patient_data_quality_review_items
WHERE review_item_key = 'dq-review-retry-dead-letter-encounter-example-001';

\echo 'Enqueuing work item with max_attempts set to 2...'

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
    'dq-work-queue-retry-dead-letter-001',
    'patient_data_quality_review',
    'patient_data_quality_review_created',
    'dq-review-retry-dead-letter-encounter-example-001',
    'Patient/example-patient-001',
    'Encounter/example-encounter-retry-dead-letter-001',
    'high',
    'ready',
    jsonb_build_object(
        'review_item_key', 'dq-review-retry-dead-letter-encounter-example-001',
        'patient_reference', 'Patient/example-patient-001',
        'encounter_reference', 'Encounter/example-encounter-retry-dead-letter-001',
        'requested_worker_action', 'prepare_for_data_quality_review',
        'retry_validation', true,
        'synthetic_validation', true
    ),
    2
);

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
SELECT
    work_item_id,
    work_item_key,
    NULL,
    'ready',
    'created',
    'system',
    'Created durable retry/dead-letter work queue item from patient data quality review item',
    jsonb_build_object(
        'source_review_item_key', source_review_item_key,
        'max_attempts', max_attempts
    )
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001';

\echo 'Worker attempts first claim...'

WITH claimed AS (
    SELECT work_item_id
    FROM data_quality_work_queue
    WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
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
    locked_by = 'synthetic_queue_worker_retry_001',
    attempt_count = attempt_count + 1,
    updated_at = NOW()
FROM claimed
WHERE queue.work_item_id = claimed.work_item_id;

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
SELECT
    work_item_id,
    work_item_key,
    'ready',
    'processing',
    'claimed',
    'synthetic_queue_worker_retry_001',
    'Worker claimed retry/dead-letter validation item for first processing attempt',
    jsonb_build_object(
        'worker_id', 'synthetic_queue_worker_retry_001',
        'attempt_count', attempt_count,
        'claim_pattern', 'FOR UPDATE SKIP LOCKED'
    )
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'processing'
  AND locked_by = 'synthetic_queue_worker_retry_001'
  AND attempt_count = 1;

\echo 'Simulating first worker failure...'

UPDATE data_quality_work_queue
SET
    status = 'failed',
    error_message = 'Simulated transient reconciliation preparation failure on first attempt',
    updated_at = NOW()
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'processing'
  AND attempt_count = 1;

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
SELECT
    work_item_id,
    work_item_key,
    'processing',
    'failed',
    'failed',
    'synthetic_queue_worker_retry_001',
    'Worker failed first processing attempt; item remains eligible for retry',
    jsonb_build_object(
        'worker_id', 'synthetic_queue_worker_retry_001',
        'attempt_count', attempt_count,
        'error_message', error_message,
        'retryable', true
    )
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'failed'
  AND attempt_count = 1;

\echo 'Scheduling retry because attempt_count is below max_attempts...'

UPDATE data_quality_work_queue
SET
    status = 'ready',
    available_at = NOW(),
    locked_at = NULL,
    locked_by = NULL,
    updated_at = NOW()
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'failed'
  AND attempt_count < max_attempts;

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
SELECT
    work_item_id,
    work_item_key,
    'failed',
    'ready',
    'retry_scheduled',
    'queue_retry_policy',
    'Retry scheduled because attempt_count is below max_attempts',
    jsonb_build_object(
        'attempt_count', attempt_count,
        'max_attempts', max_attempts,
        'retry_available_immediately_for_validation', true
    )
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'ready'
  AND attempt_count = 1;

\echo 'Worker attempts second claim...'

WITH claimed AS (
    SELECT work_item_id
    FROM data_quality_work_queue
    WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
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
    locked_by = 'synthetic_queue_worker_retry_002',
    attempt_count = attempt_count + 1,
    updated_at = NOW()
FROM claimed
WHERE queue.work_item_id = claimed.work_item_id;

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
SELECT
    work_item_id,
    work_item_key,
    'ready',
    'processing',
    'claimed',
    'synthetic_queue_worker_retry_002',
    'Worker claimed retry/dead-letter validation item for second processing attempt',
    jsonb_build_object(
        'worker_id', 'synthetic_queue_worker_retry_002',
        'attempt_count', attempt_count,
        'claim_pattern', 'FOR UPDATE SKIP LOCKED'
    )
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'processing'
  AND locked_by = 'synthetic_queue_worker_retry_002'
  AND attempt_count = 2;

\echo 'Simulating second worker failure at max attempts...'

UPDATE data_quality_work_queue
SET
    status = 'failed',
    error_message = 'Simulated persistent reconciliation preparation failure after max attempts',
    updated_at = NOW()
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'processing'
  AND attempt_count = max_attempts;

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
SELECT
    work_item_id,
    work_item_key,
    'processing',
    'failed',
    'failed',
    'synthetic_queue_worker_retry_002',
    'Worker failed second processing attempt at max attempts',
    jsonb_build_object(
        'worker_id', 'synthetic_queue_worker_retry_002',
        'attempt_count', attempt_count,
        'max_attempts', max_attempts,
        'error_message', error_message,
        'retryable', false
    )
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'failed'
  AND attempt_count = max_attempts;

\echo 'Moving work item to dead_letter after max attempts reached...'

UPDATE data_quality_work_queue
SET
    status = 'dead_letter',
    locked_at = NULL,
    locked_by = NULL,
    processed_at = NOW(),
    updated_at = NOW()
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'failed'
  AND attempt_count >= max_attempts;

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
SELECT
    work_item_id,
    work_item_key,
    'failed',
    'dead_letter',
    'moved_to_dead_letter',
    'queue_retry_policy',
    'Moved work item to dead_letter after max attempts were reached',
    jsonb_build_object(
        'attempt_count', attempt_count,
        'max_attempts', max_attempts,
        'final_error_message', error_message
    )
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
  AND status = 'dead_letter';

\echo 'Current retry/dead-letter work queue item:'

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
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001';

\echo 'Retry/dead-letter work queue history:'

SELECT
    work_item_key,
    previous_status,
    new_status,
    action_type,
    action_by,
    action_note
FROM data_quality_work_queue_history
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001'
ORDER BY history_id;

\echo 'Source review item remains unchanged after retry/dead-letter processing:'

SELECT
    review_item_key,
    patient_reference,
    encounter_reference,
    review_priority,
    review_status,
    assigned_role,
    assigned_to
FROM patient_data_quality_review_items
WHERE review_item_key = 'dq-review-retry-dead-letter-encounter-example-001';

\echo 'Expected retry attempt assertion:'

SELECT
    CASE
        WHEN status = 'dead_letter'
         AND attempt_count = 2
         AND max_attempts = 2
         AND processed_at IS NOT NULL
        THEN 'passed'
        ELSE 'failed'
    END AS retry_attempt_assertion
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001';

\echo 'Expected dead-letter assertion:'

SELECT
    CASE
        WHEN status = 'dead_letter'
         AND error_message = 'Simulated persistent reconciliation preparation failure after max attempts'
        THEN 'passed'
        ELSE 'failed'
    END AS dead_letter_assertion
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001';

\echo 'Expected retry history assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 7
         AND COUNT(*) FILTER (WHERE action_type = 'created') = 1
         AND COUNT(*) FILTER (WHERE action_type = 'claimed') = 2
         AND COUNT(*) FILTER (WHERE action_type = 'failed') = 2
         AND COUNT(*) FILTER (WHERE action_type = 'retry_scheduled') = 1
         AND COUNT(*) FILTER (WHERE action_type = 'moved_to_dead_letter') = 1
        THEN 'passed'
        ELSE 'failed'
    END AS retry_history_assertion
FROM data_quality_work_queue_history
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001';

\echo 'Expected review item unchanged assertion:'

SELECT
    CASE
        WHEN review_status = 'pending_review'
         AND review_priority = 'high'
         AND assigned_role = 'Data Quality Expert'
        THEN 'passed'
        ELSE 'failed'
    END AS review_item_unchanged_assertion
FROM patient_data_quality_review_items
WHERE review_item_key = 'dq-review-retry-dead-letter-encounter-example-001';

\echo 'Expected queue linkage assertion:'

SELECT
    CASE
        WHEN source_review_item_key = 'dq-review-retry-dead-letter-encounter-example-001'
         AND patient_reference = 'Patient/example-patient-001'
         AND encounter_reference = 'Encounter/example-encounter-retry-dead-letter-001'
        THEN 'passed'
        ELSE 'failed'
    END AS queue_linkage_assertion
FROM data_quality_work_queue
WHERE work_item_key = 'dq-work-queue-retry-dead-letter-001';

ROLLBACK;