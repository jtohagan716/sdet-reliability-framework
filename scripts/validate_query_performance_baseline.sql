BEGIN;

\echo 'Cleaning previous query performance baseline validation records if present...'

DELETE FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-perf-baseline-work-%';

DELETE FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-perf-baseline-work-%';

DELETE FROM patient_data_quality_review_actions
WHERE review_item_id IN (
    SELECT review_item_id
    FROM patient_data_quality_review_items
    WHERE review_item_key LIKE 'dq-perf-baseline-review-%'
);

DELETE FROM patient_data_quality_review_items
WHERE review_item_key LIKE 'dq-perf-baseline-review-%';

\echo 'Creating synthetic patient data quality review records for performance baseline...'

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
SELECT
    'dq-perf-baseline-review-' || LPAD(series_id::text, 3, '0') AS review_item_key,
    'performance_baseline',
    'Patient/performance-baseline-patient-' || LPAD(series_id::text, 3, '0') AS patient_reference,
    'Encounter/performance-baseline-encounter-' || LPAD(series_id::text, 3, '0') AS encounter_reference,
    'performance-baseline-event-' || LPAD(series_id::text, 3, '0') AS related_event_id,
    'Performance baseline review item for API/database query measurement',
    'Synthetic review item used to measure query behavior for pending high-priority work',
    CASE
        WHEN series_id <= 10 THEN 'high'
        WHEN series_id <= 15 THEN 'medium'
        ELSE 'low'
    END AS review_priority,
    CASE
        WHEN series_id <= 15 THEN 'pending_review'
        ELSE 'closed'
    END AS review_status,
    'Data Quality Expert',
    'synthetic_performance_reviewer',
    jsonb_build_object(
        'performance_baseline', true,
        'series_id', series_id,
        'synthetic_validation', true
    )
FROM generate_series(1, 25) AS series_id;

\echo 'Creating matching queue records for performance baseline review items...'

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
    max_attempts
)
SELECT
    'dq-perf-baseline-work-' || LPAD(series_id::text, 3, '0') AS work_item_key,
    'patient_data_quality_review',
    'patient_data_quality_review_created',
    'dq-perf-baseline-review-' || LPAD(series_id::text, 3, '0') AS source_review_item_key,
    'Patient/performance-baseline-patient-' || LPAD(series_id::text, 3, '0') AS patient_reference,
    'Encounter/performance-baseline-encounter-' || LPAD(series_id::text, 3, '0') AS encounter_reference,
    CASE
        WHEN series_id <= 10 THEN 'high'
        WHEN series_id <= 15 THEN 'medium'
        ELSE 'low'
    END AS priority,
    CASE
        WHEN series_id <= 8 THEN 'ready'
        WHEN series_id <= 10 THEN 'processing'
        WHEN series_id <= 12 THEN 'completed'
        WHEN series_id <= 15 THEN 'dead_letter'
        ELSE 'completed'
    END AS status,
    jsonb_build_object(
        'performance_baseline', true,
        'series_id', series_id,
        'synthetic_validation', true
    ),
    CASE
        WHEN series_id <= 8 THEN 0
        WHEN series_id <= 10 THEN 1
        WHEN series_id <= 12 THEN 1
        WHEN series_id <= 15 THEN 2
        ELSE 1
    END AS attempt_count,
    3 AS max_attempts
FROM generate_series(1, 25) AS series_id;

\echo 'Running ANALYZE so PostgreSQL has current statistics for the baseline data...'

ANALYZE patient_data_quality_review_items;
ANALYZE data_quality_work_queue;

\echo 'Baseline query purpose: pending high-priority review items with related queue status.'

\echo 'Capturing EXPLAIN ANALYZE plan with buffers...'

EXPLAIN (ANALYZE, BUFFERS, VERBOSE)
SELECT
    review.review_item_key,
    review.patient_reference,
    review.encounter_reference,
    review.review_priority,
    review.review_status,
    review.assigned_role,
    queue.work_item_key,
    queue.status AS queue_status,
    queue.attempt_count,
    queue.max_attempts
FROM patient_data_quality_review_items AS review
LEFT JOIN data_quality_work_queue AS queue
    ON queue.source_review_item_key = review.review_item_key
WHERE review.review_status = 'pending_review'
  AND review.review_priority = 'high'
ORDER BY review.created_at ASC, review.review_item_key ASC;

\echo 'Running baseline query result check...'

SELECT
    review.review_item_key,
    review.patient_reference,
    review.encounter_reference,
    review.review_priority,
    review.review_status,
    queue.work_item_key,
    queue.status AS queue_status,
    queue.attempt_count,
    queue.max_attempts
FROM patient_data_quality_review_items AS review
LEFT JOIN data_quality_work_queue AS queue
    ON queue.source_review_item_key = review.review_item_key
WHERE review.review_status = 'pending_review'
  AND review.review_priority = 'high'
ORDER BY review.created_at ASC, review.review_item_key ASC;

\echo 'Expected baseline row count assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 10
        THEN 'passed'
        ELSE 'failed'
    END AS baseline_row_count_assertion
FROM patient_data_quality_review_items AS review
LEFT JOIN data_quality_work_queue AS queue
    ON queue.source_review_item_key = review.review_item_key
WHERE review.review_status = 'pending_review'
  AND review.review_priority = 'high';

\echo 'Expected queue linkage assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 10
         AND COUNT(queue.work_item_key) = 10
        THEN 'passed'
        ELSE 'failed'
    END AS queue_linkage_assertion
FROM patient_data_quality_review_items AS review
LEFT JOIN data_quality_work_queue AS queue
    ON queue.source_review_item_key = review.review_item_key
WHERE review.review_status = 'pending_review'
  AND review.review_priority = 'high';

\echo 'Expected queue status distribution assertion:'

SELECT
    CASE
        WHEN COUNT(*) FILTER (WHERE queue.status = 'ready') = 8
         AND COUNT(*) FILTER (WHERE queue.status = 'processing') = 2
        THEN 'passed'
        ELSE 'failed'
    END AS queue_status_distribution_assertion
FROM patient_data_quality_review_items AS review
LEFT JOIN data_quality_work_queue AS queue
    ON queue.source_review_item_key = review.review_item_key
WHERE review.review_status = 'pending_review'
  AND review.review_priority = 'high';

\echo 'Expected no tuning assertion:'

SELECT
    'passed' AS no_tuning_applied_assertion,
    'This script captures a baseline only. No indexes or configuration changes are applied.' AS note;

ROLLBACK;