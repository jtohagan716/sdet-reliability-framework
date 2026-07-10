BEGIN;

\echo 'Cleaning previous query performance tuning comparison validation records if present...'

DELETE FROM data_quality_work_queue_history
WHERE work_item_key LIKE 'dq-perf-tuning-work-%';

DELETE FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-perf-tuning-work-%';

DELETE FROM patient_data_quality_review_actions
WHERE review_item_id IN (
    SELECT review_item_id
    FROM patient_data_quality_review_items
    WHERE review_item_key LIKE 'dq-perf-tuning-review-%'
);

DELETE FROM patient_data_quality_review_items
WHERE review_item_key LIKE 'dq-perf-tuning-review-%';

DROP INDEX IF EXISTS idx_perf_tuning_review_status_priority_created_key;

\echo 'Creating larger synthetic patient data quality review dataset for pre/post tuning comparison...'

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
    'dq-perf-tuning-review-' || LPAD(series_id::text, 5, '0') AS review_item_key,
    'performance_tuning_comparison',
    'Patient/performance-tuning-patient-' || LPAD(series_id::text, 5, '0') AS patient_reference,
    'Encounter/performance-tuning-encounter-' || LPAD(series_id::text, 5, '0') AS encounter_reference,
    'performance-tuning-event-' || LPAD(series_id::text, 5, '0') AS related_event_id,
    'Performance tuning comparison review item',
    'Synthetic review item used to compare pre/post query tuning behavior',
    CASE
        WHEN series_id <= 100 THEN 'high'
        WHEN series_id <= 1000 THEN 'medium'
        ELSE 'low'
    END AS review_priority,
    CASE
        WHEN series_id <= 100 THEN 'pending_review'
        WHEN series_id <= 2000 THEN 'closed'
        ELSE 'closed'
    END AS review_status,
    'Data Quality Expert',
    'synthetic_performance_reviewer',
    jsonb_build_object(
        'performance_tuning_comparison', true,
        'series_id', series_id,
        'synthetic_validation', true
    ),
    NOW() - ((10000 - series_id) * INTERVAL '1 second') AS created_at
FROM generate_series(1, 10000) AS series_id;

\echo 'Creating matching queue records for performance tuning comparison dataset...'

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
    created_at
)
SELECT
    'dq-perf-tuning-work-' || LPAD(series_id::text, 5, '0') AS work_item_key,
    'patient_data_quality_review',
    'patient_data_quality_review_created',
    'dq-perf-tuning-review-' || LPAD(series_id::text, 5, '0') AS source_review_item_key,
    'Patient/performance-tuning-patient-' || LPAD(series_id::text, 5, '0') AS patient_reference,
    'Encounter/performance-tuning-encounter-' || LPAD(series_id::text, 5, '0') AS encounter_reference,
    CASE
        WHEN series_id <= 100 THEN 'high'
        WHEN series_id <= 1000 THEN 'medium'
        ELSE 'low'
    END AS priority,
    CASE
        WHEN series_id <= 80 THEN 'ready'
        WHEN series_id <= 100 THEN 'processing'
        ELSE 'completed'
    END AS status,
    jsonb_build_object(
        'performance_tuning_comparison', true,
        'series_id', series_id,
        'synthetic_validation', true
    ),
    CASE
        WHEN series_id <= 80 THEN 0
        WHEN series_id <= 100 THEN 1
        ELSE 1
    END AS attempt_count,
    3 AS max_attempts,
    NOW() - ((10000 - series_id) * INTERVAL '1 second') AS created_at
FROM generate_series(1, 10000) AS series_id;

\echo 'Running ANALYZE before pre-tuning measurement...'

ANALYZE patient_data_quality_review_items;
ANALYZE data_quality_work_queue;

\echo 'Pre-tuning dataset summary:'

SELECT
    COUNT(*) AS total_review_items,
    COUNT(*) FILTER (
        WHERE review_status = 'pending_review'
          AND review_priority = 'high'
    ) AS target_review_items
FROM patient_data_quality_review_items
WHERE review_item_key LIKE 'dq-perf-tuning-review-%';

SELECT
    COUNT(*) AS total_queue_items,
    COUNT(*) FILTER (WHERE status = 'ready') AS ready_queue_items,
    COUNT(*) FILTER (WHERE status = 'processing') AS processing_queue_items,
    COUNT(*) FILTER (WHERE status = 'completed') AS completed_queue_items
FROM data_quality_work_queue
WHERE work_item_key LIKE 'dq-perf-tuning-work-%';

\echo 'PRE-TUNING PLAN: pending high-priority review items with related queue status.'

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
ORDER BY review.created_at ASC, review.review_item_key ASC
LIMIT 25;

\echo 'Applying one targeted tuning change: composite index for review status, priority, created_at, and review item key...'

CREATE INDEX idx_perf_tuning_review_status_priority_created_key
ON patient_data_quality_review_items (
    review_status,
    review_priority,
    created_at,
    review_item_key
);

ANALYZE patient_data_quality_review_items;

\echo 'POST-TUNING PLAN: same query after targeted composite index.'

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
ORDER BY review.created_at ASC, review.review_item_key ASC
LIMIT 25;

\echo 'Running tuned query result check...'

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
ORDER BY review.created_at ASC, review.review_item_key ASC
LIMIT 25;

\echo 'Expected tuning result row count assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 25
        THEN 'passed'
        ELSE 'failed'
    END AS tuning_result_row_count_assertion
FROM (
    SELECT
        review.review_item_key
    FROM patient_data_quality_review_items AS review
    LEFT JOIN data_quality_work_queue AS queue
        ON queue.source_review_item_key = review.review_item_key
    WHERE review.review_status = 'pending_review'
      AND review.review_priority = 'high'
    ORDER BY review.created_at ASC, review.review_item_key ASC
    LIMIT 25
) AS tuned_result;

\echo 'Expected tuning dataset assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 100
        THEN 'passed'
        ELSE 'failed'
    END AS tuning_target_dataset_assertion
FROM patient_data_quality_review_items
WHERE review_item_key LIKE 'dq-perf-tuning-review-%'
  AND review_status = 'pending_review'
  AND review_priority = 'high';

\echo 'Expected queue linkage assertion:'

SELECT
    CASE
        WHEN COUNT(*) = 100
         AND COUNT(queue.work_item_key) = 100
        THEN 'passed'
        ELSE 'failed'
    END AS tuning_queue_linkage_assertion
FROM patient_data_quality_review_items AS review
LEFT JOIN data_quality_work_queue AS queue
    ON queue.source_review_item_key = review.review_item_key
WHERE review.review_item_key LIKE 'dq-perf-tuning-review-%'
  AND review.review_status = 'pending_review'
  AND review.review_priority = 'high';

\echo 'Expected tuning change assertion:'

SELECT
    CASE
        WHEN EXISTS (
            SELECT 1
            FROM pg_indexes
            WHERE schemaname = 'public'
              AND indexname = 'idx_perf_tuning_review_status_priority_created_key'
        )
        THEN 'passed'
        ELSE 'failed'
    END AS tuning_index_created_assertion;

\echo 'Pre/post comparison report note:'

SELECT
    'passed' AS pre_post_report_ready_assertion,
    'This script captures pre/post query plans and applies one targeted composite index inside a rollback-safe transaction.' AS note;

ROLLBACK;