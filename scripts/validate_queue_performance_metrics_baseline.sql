BEGIN;

\echo 'QUEUE_PERFORMANCE_METRICS_BASELINE_START'
\echo 'Cleaning previous queue performance metrics baseline records if present...'

DELETE FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

DELETE FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

DELETE FROM patient_data_quality_review_actions
WHERE review_item_id IN (
    SELECT review_item_id
    FROM patient_data_quality_review_items
    WHERE review_item_key LIKE 'dq-review-queue-metrics-baseline-%'
);

DELETE FROM patient_data_quality_review_items
WHERE review_item_key LIKE 'dq-review-queue-metrics-baseline-%';

\echo 'Creating synthetic patient data quality review records for queue metrics baseline...'

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
    details,
    created_at
)
SELECT
    'dq-review-queue-metrics-baseline-' || LPAD(series_id::text, 3, '0') AS review_item_key,
    'queue_performance_metrics_baseline' AS review_source,
    'Patient/queue-metrics-baseline-patient-' || LPAD(series_id::text, 3, '0') AS patient_reference,
    'Encounter/queue-metrics-baseline-encounter-' || LPAD(series_id::text, 3, '0') AS encounter_reference,
    'queue-metrics-baseline-event-' || LPAD(series_id::text, 3, '0') AS related_event_id,
    'Synthetic review item used for queue performance metrics baseline' AS review_reason,
    'Synthetic item used to measure queue health, retry pressure, backlog age, and dead-letter visibility' AS risk_summary,
    CASE
        WHEN series_id <= 10 THEN 'high'
        WHEN series_id <= 20 THEN 'medium'
        ELSE 'low'
    END AS review_priority,
    CASE
        WHEN series_id <= 15 THEN 'pending_review'
        WHEN series_id <= 22 THEN 'closed'
        ELSE 'pending_review'
    END AS review_status,
    'Data Quality Expert' AS assigned_role,
    'synthetic_queue_metrics_reviewer' AS assigned_to,
    jsonb_build_object(
        'queue_metrics_baseline', true,
        'series_id', series_id,
        'synthetic_validation', true
    ) AS details,
    NOW() - (series_id * INTERVAL '2 minutes') AS created_at
FROM generate_series(1, 30) AS series_id;

\echo 'Creating synthetic work queue records with deterministic status distribution...'

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
    attempt_count,
    max_attempts,
    available_at,
    locked_at,
    locked_by,
    processed_at,
    error_message,
    created_at,
    updated_at
)
SELECT
    'dq-work-queue-metrics-baseline-' || LPAD(series_id::text, 3, '0') AS work_item_key,
    'patient_data_quality_review' AS queue_name,
    'patient_data_quality_review_created' AS event_type,
    'dq-review-queue-metrics-baseline-' || LPAD(series_id::text, 3, '0') AS source_review_item_key,
    'Patient/queue-metrics-baseline-patient-' || LPAD(series_id::text, 3, '0') AS patient_reference,
    'Encounter/queue-metrics-baseline-encounter-' || LPAD(series_id::text, 3, '0') AS encounter_reference,
    CASE
        WHEN series_id <= 10 THEN 'high'
        WHEN series_id <= 20 THEN 'medium'
        ELSE 'low'
    END AS priority,
    CASE
        WHEN series_id <= 10 THEN 'ready'
        WHEN series_id <= 15 THEN 'processing'
        WHEN series_id <= 22 THEN 'completed'
        WHEN series_id <= 26 THEN 'failed'
        ELSE 'dead_letter'
    END AS status,
    jsonb_build_object(
        'queue_metrics_baseline', true,
        'series_id', series_id,
        'source_review_item_key', 'dq-review-queue-metrics-baseline-' || LPAD(series_id::text, 3, '0'),
        'requested_worker_action', 'measure_queue_health',
        'synthetic_validation', true
    ) AS payload,
    CASE
        WHEN series_id <= 10 THEN 0
        WHEN series_id <= 22 THEN 1
        WHEN series_id <= 24 THEN 1
        WHEN series_id <= 26 THEN 2
        ELSE 3
    END AS attempt_count,
    3 AS max_attempts,
    CASE
        WHEN series_id <= 10 THEN NOW() - (series_id * INTERVAL '3 minutes')
        WHEN series_id <= 15 THEN NOW() - ((series_id - 10) * INTERVAL '5 minutes')
        WHEN series_id <= 22 THEN NOW() - ((series_id - 15) * INTERVAL '4 minutes')
        WHEN series_id <= 26 THEN NOW() - ((series_id - 22) * INTERVAL '6 minutes')
        ELSE NOW() - ((series_id - 26) * INTERVAL '8 minutes')
    END AS available_at,
    CASE
        WHEN series_id BETWEEN 11 AND 15 THEN NOW() - ((series_id - 10) * INTERVAL '5 minutes')
        ELSE NULL
    END AS locked_at,
    CASE
        WHEN series_id BETWEEN 11 AND 15 THEN 'synthetic_queue_metrics_worker_' || LPAD((series_id - 10)::text, 3, '0')
        ELSE NULL
    END AS locked_by,
    CASE
        WHEN series_id BETWEEN 16 AND 22 THEN NOW() - ((series_id - 15) * INTERVAL '4 minutes')
        WHEN series_id >= 27 THEN NOW() - ((series_id - 26) * INTERVAL '8 minutes')
        ELSE NULL
    END AS processed_at,
    CASE
        WHEN series_id BETWEEN 23 AND 26 THEN 'Synthetic retryable queue failure for metrics baseline'
        WHEN series_id >= 27 THEN 'Synthetic persistent queue failure moved to dead-letter for metrics baseline'
        ELSE NULL
    END AS error_message,
    NOW() - (series_id * INTERVAL '2 minutes') AS created_at,
    NOW() - (series_id * INTERVAL '1 minute') AS updated_at
FROM generate_series(1, 30) AS series_id;

\echo 'Creating synthetic queue history records for metrics baseline...'

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
    status,
    'created',
    'queue_metrics_baseline_seed',
    'Created synthetic queue item for queue performance metrics baseline',
    jsonb_build_object(
        'queue_metrics_baseline', true,
        'status_at_creation', status,
        'attempt_count', attempt_count,
        'max_attempts', max_attempts
    )
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

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
    COALESCE(locked_by, 'synthetic_queue_metrics_worker'),
    'Synthetic worker claim event used for queue metrics baseline',
    jsonb_build_object(
        'queue_metrics_baseline', true,
        'attempt_count', attempt_count,
        'claim_pattern', 'FOR UPDATE SKIP LOCKED'
    )
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status IN ('processing', 'completed', 'failed', 'dead_letter');

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
    'completed',
    'completed',
    'synthetic_queue_metrics_worker',
    'Synthetic completed event used for queue metrics baseline',
    jsonb_build_object(
        'queue_metrics_baseline', true,
        'attempt_count', attempt_count
    )
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status = 'completed';

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
    'synthetic_queue_metrics_worker',
    'Synthetic failed event used for queue metrics baseline',
    jsonb_build_object(
        'queue_metrics_baseline', true,
        'attempt_count', attempt_count,
        'max_attempts', max_attempts,
        'retryable', attempt_count < max_attempts,
        'error_message', error_message
    )
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status IN ('failed', 'dead_letter');

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
    'Synthetic retry scheduled event used for queue metrics baseline',
    jsonb_build_object(
        'queue_metrics_baseline', true,
        'attempt_count', attempt_count,
        'max_attempts', max_attempts,
        'retryable', true
    )
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
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
    'dead_letter',
    'moved_to_dead_letter',
    'queue_retry_policy',
    'Synthetic dead-letter event used for queue metrics baseline',
    jsonb_build_object(
        'queue_metrics_baseline', true,
        'attempt_count', attempt_count,
        'max_attempts', max_attempts,
        'final_error_message', error_message
    )
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status = 'dead_letter';

\echo 'Queue status distribution metrics:'

SELECT COUNT(*) AS queue_total_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE status = 'ready') AS queue_ready_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE status = 'processing') AS queue_processing_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE status = 'completed') AS queue_completed_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE status = 'failed') AS queue_failed_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE status = 'dead_letter') AS queue_dead_letter_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Queue retry and attempt metrics:'

SELECT COUNT(*) AS queue_retry_eligible_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status = 'failed'
  AND attempt_count < max_attempts;

SELECT MAX(attempt_count) AS queue_max_attempt_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT ROUND(AVG(attempt_count)::numeric, 2) AS queue_average_attempt_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Queue backlog age metrics:'

SELECT ROUND(EXTRACT(EPOCH FROM (NOW() - MIN(available_at))) / 60.0, 2) AS oldest_ready_item_age_minutes
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status = 'ready';

SELECT ROUND(EXTRACT(EPOCH FROM (NOW() - MIN(locked_at))) / 60.0, 2) AS oldest_processing_item_age_minutes
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status = 'processing';

SELECT
    COUNT(*) FILTER (WHERE created_at >= NOW() - INTERVAL '15 minutes') AS queue_age_under_15_min_count,
    COUNT(*) FILTER (WHERE created_at < NOW() - INTERVAL '15 minutes'
                     AND created_at >= NOW() - INTERVAL '45 minutes') AS queue_age_15_to_45_min_count,
    COUNT(*) FILTER (WHERE created_at < NOW() - INTERVAL '45 minutes') AS queue_age_over_45_min_count
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Queue history action metrics:'

SELECT COUNT(*) FILTER (WHERE action_type = 'created') AS history_created_count
FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE action_type = 'claimed') AS history_claimed_count
FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE action_type = 'completed') AS history_completed_count
FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE action_type = 'failed') AS history_failed_count
FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE action_type = 'retry_scheduled') AS history_retry_scheduled_count
FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

SELECT COUNT(*) FILTER (WHERE action_type = 'moved_to_dead_letter') AS history_moved_to_dead_letter_count
FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Expected queue total assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 30
        THEN 'passed'
        ELSE 'failed'
    END AS queue_total_count_assertion
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Expected queue status distribution assertion:'

SELECT
    CASE
        WHEN COUNT(*) FILTER (WHERE status = 'ready') = 10
         AND COUNT(*) FILTER (WHERE status = 'processing') = 5
         AND COUNT(*) FILTER (WHERE status = 'completed') = 7
         AND COUNT(*) FILTER (WHERE status = 'failed') = 4
         AND COUNT(*) FILTER (WHERE status = 'dead_letter') = 4
        THEN 'passed'
        ELSE 'failed'
    END AS queue_status_distribution_assertion
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Expected retry pressure assertion:'

SELECT
    CASE
        WHEN COUNT(*) FILTER (
            WHERE status = 'failed'
              AND attempt_count < max_attempts
        ) = 4
         AND MAX(attempt_count) = 3
         AND ROUND(AVG(attempt_count)::numeric, 2) > 0
        THEN 'passed'
        ELSE 'failed'
    END AS queue_retry_pressure_assertion
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Expected dead-letter assertion:'

SELECT
    CASE
        WHEN COUNT(*) FILTER (WHERE status = 'dead_letter') = 4
         AND COUNT(*) FILTER (
            WHERE status = 'dead_letter'
              AND attempt_count >= max_attempts
              AND processed_at IS NOT NULL
         ) = 4
        THEN 'passed'
        ELSE 'failed'
    END AS queue_dead_letter_assertion
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Expected queue age metrics assertion:'

SELECT
    CASE
        WHEN ROUND(EXTRACT(EPOCH FROM (NOW() - MIN(available_at))) / 60.0, 2) >= 25
        THEN 'passed'
        ELSE 'failed'
    END AS queue_age_metrics_assertion
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status = 'ready';

\echo 'Expected processing age metrics assertion:'

SELECT
    CASE
        WHEN ROUND(EXTRACT(EPOCH FROM (NOW() - MIN(locked_at))) / 60.0, 2) >= 20
        THEN 'passed'
        ELSE 'failed'
    END AS queue_processing_age_metrics_assertion
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%'
  AND status = 'processing';

\echo 'Expected queue history metrics assertion:'

SELECT
    CASE
        WHEN COUNT(*) FILTER (WHERE action_type = 'created') = 30
         AND COUNT(*) FILTER (WHERE action_type = 'claimed') = 20
         AND COUNT(*) FILTER (WHERE action_type = 'completed') = 7
         AND COUNT(*) FILTER (WHERE action_type = 'failed') = 8
         AND COUNT(*) FILTER (WHERE action_type = 'retry_scheduled') = 4
         AND COUNT(*) FILTER (WHERE action_type = 'moved_to_dead_letter') = 4
        THEN 'passed'
        ELSE 'failed'
    END AS queue_history_metrics_assertion
FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-work-queue-metrics-baseline-%';

\echo 'Queue metrics baseline note:'
\echo 'This script captures queue health metrics only. It does not run a throughput or load test.'

ROLLBACK;