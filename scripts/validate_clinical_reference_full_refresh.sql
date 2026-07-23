\set ON_ERROR_STOP on

BEGIN;

\echo 'Preparing deterministic full-refresh test data...'

/*
 * These changes occur inside a transaction and are rolled back at the end.
 * Clearing the controlled records gives the test a known starting state.
 */
DELETE FROM facility_cache.appointment_type_reference;

DELETE FROM central_repository.appointment_type_reference;

/*
 * The checkpoint must be removed before its referenced synchronization run.
 * The transaction rollback restores any checkpoint that existed previously.
 */
DELETE FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';

DELETE FROM sync_control.sync_table_result
WHERE sync_run_id IN (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'dddddddd-dddd-dddd-dddd-dddddddddddd'
);

DELETE FROM sync_control.sync_run
WHERE sync_run_id IN (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'dddddddd-dddd-dddd-dddd-dddddddddddd'
);


\echo 'Creating a previously successful run for stale cache data...'

INSERT INTO sync_control.sync_run (
    sync_run_id,
    reference_domain,
    load_mode,
    run_status,
    processing_window_started_at,
    processing_window_deadline_at,
    started_at,
    completed_at,
    source_row_count,
    inserted_row_count,
    target_row_count,
    reconciliation_status
)
VALUES (
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    'appointment_type',
    'full_refresh',
    'completed',
    TIMESTAMPTZ '2026-07-22 00:00:00+00',
    TIMESTAMPTZ '2026-07-22 05:00:00+00',
    TIMESTAMPTZ '2026-07-22 00:10:00+00',
    TIMESTAMPTZ '2026-07-22 00:15:00+00',
    1,
    1,
    1,
    'passed'
);


\echo 'Creating an intentionally stale facility-cache record...'

INSERT INTO facility_cache.appointment_type_reference (
    appointment_type_code,
    display_name,
    description,
    active_flag,
    effective_date,
    expiration_date,
    source_updated_at,
    source_version,
    sync_run_id,
    synced_at
)
VALUES (
    'STALE',
    'Obsolete Appointment',
    'This record must be removed by the full refresh.',
    FALSE,
    DATE '2020-01-01',
    DATE '2021-01-01',
    TIMESTAMPTZ '2026-07-22 00:00:00+00',
    1,
    'cccccccc-cccc-cccc-cccc-cccccccccccc',
    TIMESTAMPTZ '2026-07-22 00:15:00+00'
);


\echo 'Loading a deterministic five-row source snapshot...'

INSERT INTO central_repository.appointment_type_reference (
    appointment_type_code,
    display_name,
    description,
    active_flag,
    effective_date,
    expiration_date,
    source_updated_at,
    source_version
)
VALUES
    (
        'ROUTINE',
        'Routine Visit',
        'Standard scheduled clinical appointment.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:00+00',
        1
    ),
    (
        'URGENT',
        'Urgent Visit',
        'Time-sensitive appointment requiring prompt evaluation.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        1
    ),
    (
        'TELEHEALTH',
        'Telehealth Visit',
        'Remote clinical appointment.',
        TRUE,
        DATE '2026-02-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:03:00+00',
        2
    ),
    (
        'FOLLOWUP',
        'Follow-up Visit',
        'Follow-up appointment after prior treatment.',
        TRUE,
        DATE '2026-01-15',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:04:00+00',
        3
    ),
    (
        'LEGACY',
        'Legacy Appointment',
        'Inactive historical appointment type.',
        FALSE,
        DATE '2020-01-01',
        DATE '2025-12-31',
        TIMESTAMPTZ '2026-07-23 00:05:00+00',
        4
    );


\echo 'Executing the full-refresh procedure...'

CALL sync_control.full_refresh_appointment_type_reference (
    'dddddddd-dddd-dddd-dddd-dddddddddddd',
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00'
);


\echo 'Validating full-refresh behavior...'

DO $validation$
DECLARE
    v_source_count BIGINT;
    v_cache_count BIGINT;
    v_stale_count BIGINT;
    v_new_run_cache_count BIGINT;
    v_other_run_cache_count BIGINT;
    v_source_minus_cache_count BIGINT;
    v_cache_minus_source_count BIGINT;
    v_distinct_synced_at_count BIGINT;
    v_checkpoint_count BIGINT;
    v_completed_run_count BIGINT;
    v_completed_table_result_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_source_count
    FROM central_repository.appointment_type_reference;

    SELECT COUNT(*)
    INTO v_cache_count
    FROM facility_cache.appointment_type_reference;

    IF v_source_count <> 5 OR v_cache_count <> 5 THEN
        RAISE EXCEPTION
            'Expected five source and five cache records; '
            'source=%, cache=%',
            v_source_count,
            v_cache_count;
    END IF;

    RAISE NOTICE
        'full_refresh_row_count_assertion: passed';


    SELECT COUNT(*)
    INTO v_stale_count
    FROM facility_cache.appointment_type_reference
    WHERE appointment_type_code = 'STALE';

    IF v_stale_count <> 0 THEN
        RAISE EXCEPTION
            'Stale cache record was not removed';
    END IF;

    RAISE NOTICE
        'stale_cache_replacement_assertion: passed';


    SELECT COUNT(*)
    INTO v_new_run_cache_count
    FROM facility_cache.appointment_type_reference
    WHERE sync_run_id =
        'dddddddd-dddd-dddd-dddd-dddddddddddd';

    SELECT COUNT(*)
    INTO v_other_run_cache_count
    FROM facility_cache.appointment_type_reference
    WHERE sync_run_id <>
        'dddddddd-dddd-dddd-dddd-dddddddddddd';

    IF v_new_run_cache_count <> 5
       OR v_other_run_cache_count <> 0 THEN
        RAISE EXCEPTION
            'Cache synchronization metadata is incorrect; '
            'new_run=%, other_run=%',
            v_new_run_cache_count,
            v_other_run_cache_count;
    END IF;


    SELECT COUNT(DISTINCT synced_at)
    INTO v_distinct_synced_at_count
    FROM facility_cache.appointment_type_reference;

    IF v_distinct_synced_at_count <> 1 THEN
        RAISE EXCEPTION
            'Expected one common cache synchronization timestamp; '
            'found %',
            v_distinct_synced_at_count;
    END IF;

    RAISE NOTICE
        'cache_sync_metadata_assertion: passed';


    SELECT COUNT(*)
    INTO v_source_minus_cache_count
    FROM (
        SELECT
            appointment_type_code,
            display_name,
            description,
            active_flag,
            effective_date,
            expiration_date,
            source_updated_at,
            source_version
        FROM central_repository.appointment_type_reference

        EXCEPT

        SELECT
            appointment_type_code,
            display_name,
            description,
            active_flag,
            effective_date,
            expiration_date,
            source_updated_at,
            source_version
        FROM facility_cache.appointment_type_reference
    ) AS source_minus_cache;


    SELECT COUNT(*)
    INTO v_cache_minus_source_count
    FROM (
        SELECT
            appointment_type_code,
            display_name,
            description,
            active_flag,
            effective_date,
            expiration_date,
            source_updated_at,
            source_version
        FROM facility_cache.appointment_type_reference

        EXCEPT

        SELECT
            appointment_type_code,
            display_name,
            description,
            active_flag,
            effective_date,
            expiration_date,
            source_updated_at,
            source_version
        FROM central_repository.appointment_type_reference
    ) AS cache_minus_source;

    IF v_source_minus_cache_count <> 0
       OR v_cache_minus_source_count <> 0 THEN
        RAISE EXCEPTION
            'Source and cache contents do not match; '
            'source_minus_cache=%, cache_minus_source=%',
            v_source_minus_cache_count,
            v_cache_minus_source_count;
    END IF;

    RAISE NOTICE
        'bidirectional_data_reconciliation_assertion: passed';


    /*
     * The final deterministic source position is the latest timestamp
     * followed by the highest source key when timestamps are equal.
     */
    SELECT COUNT(*)
    INTO v_checkpoint_count
    FROM sync_control.sync_checkpoint
    WHERE reference_domain = 'appointment_type'
      AND last_source_updated_at =
          TIMESTAMPTZ '2026-07-23 00:05:00+00'
      AND last_source_key = 'LEGACY'
      AND last_successful_sync_run_id =
          'dddddddd-dddd-dddd-dddd-dddddddddddd'
      AND updated_at IS NOT NULL;

    IF v_checkpoint_count <> 1 THEN
        RAISE EXCEPTION
            'Full refresh checkpoint evidence is incorrect';
    END IF;

    RAISE NOTICE
        'full_refresh_checkpoint_assertion: passed';


    SELECT COUNT(*)
    INTO v_completed_run_count
    FROM sync_control.sync_run
    WHERE sync_run_id =
            'dddddddd-dddd-dddd-dddd-dddddddddddd'
      AND reference_domain = 'appointment_type'
      AND load_mode = 'full_refresh'
      AND run_status = 'completed'
      AND completed_at IS NOT NULL
      AND source_row_count = 5
      AND inserted_row_count = 5
      AND target_row_count = 5
      AND reconciliation_status = 'passed'
      AND error_message IS NULL;

    IF v_completed_run_count <> 1 THEN
        RAISE EXCEPTION
            'Completed synchronization-run evidence is incorrect';
    END IF;

    RAISE NOTICE
        'sync_run_success_outcome_assertion: passed';


    SELECT COUNT(*)
    INTO v_completed_table_result_count
    FROM sync_control.sync_table_result
    WHERE sync_run_id =
            'dddddddd-dddd-dddd-dddd-dddddddddddd'
      AND source_table_name =
            'central_repository.appointment_type_reference'
      AND target_table_name =
            'facility_cache.appointment_type_reference'
      AND table_status = 'completed'
      AND completed_at IS NOT NULL
      AND source_row_count = 5
      AND inserted_row_count = 5
      AND target_row_count = 5
      AND reconciliation_status = 'passed'
      AND error_message IS NULL;

    IF v_completed_table_result_count <> 1 THEN
        RAISE EXCEPTION
            'Completed table-result evidence is incorrect';
    END IF;

    RAISE NOTICE
        'sync_table_result_success_outcome_assertion: passed';
END;
$validation$;


\echo 'Observed facility-cache contents:'

SELECT
    appointment_type_code,
    display_name,
    active_flag,
    source_version,
    sync_run_id
FROM facility_cache.appointment_type_reference
ORDER BY appointment_type_code;


\echo 'Observed synchronization-run outcome:'

SELECT
    sync_run_id,
    load_mode,
    run_status,
    source_row_count,
    inserted_row_count,
    target_row_count,
    reconciliation_status
FROM sync_control.sync_run
WHERE sync_run_id =
    'dddddddd-dddd-dddd-dddd-dddddddddddd';


\echo 'Observed per-table outcome:'

SELECT
    source_table_name,
    target_table_name,
    table_status,
    source_row_count,
    inserted_row_count,
    target_row_count,
    reconciliation_status
FROM sync_control.sync_table_result
WHERE sync_run_id =
    'dddddddd-dddd-dddd-dddd-dddddddddddd';


\echo 'Observed synchronization checkpoint:'

SELECT
    reference_domain,
    last_source_updated_at,
    last_source_key,
    last_successful_sync_run_id,
    updated_at
FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';


ROLLBACK;