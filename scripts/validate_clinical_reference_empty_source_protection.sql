\set ON_ERROR_STOP on

BEGIN;

\echo 'Preparing empty-source protection scenario...'

DELETE FROM facility_cache.appointment_type_reference;

DELETE FROM central_repository.appointment_type_reference;

/*
 * Remove the checkpoint before deleting its referenced synchronization run.
 * The final rollback restores any state that existed before this test.
 */
DELETE FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';

DELETE FROM sync_control.sync_table_result
WHERE sync_run_id IN (
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'ffffffff-ffff-ffff-ffff-ffffffffffff'
);

DELETE FROM sync_control.sync_run
WHERE sync_run_id IN (
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    'ffffffff-ffff-ffff-ffff-ffffffffffff'
);


\echo 'Creating a previously successful synchronization run...'

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
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
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


\echo 'Creating the previous successful checkpoint...'

INSERT INTO sync_control.sync_checkpoint (
    reference_domain,
    last_source_updated_at,
    last_source_key,
    last_successful_sync_run_id,
    updated_at
)
VALUES (
    'appointment_type',
    TIMESTAMPTZ '2026-07-22 00:01:00+00',
    'ROUTINE',
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    TIMESTAMPTZ '2026-07-22 00:15:00+00'
);


\echo 'Creating a valid preexisting facility-cache record...'

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
    'ROUTINE',
    'Routine Visit',
    'Previously synchronized cache record that must be preserved.',
    TRUE,
    DATE '2026-01-01',
    NULL,
    TIMESTAMPTZ '2026-07-22 00:01:00+00',
    7,
    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
    TIMESTAMPTZ '2026-07-22 00:15:00+00'
);


\echo 'Calling full refresh with an empty central source...'

CALL sync_control.full_refresh_appointment_type_reference (
    'ffffffff-ffff-ffff-ffff-ffffffffffff',
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00'
);


\echo 'Validating empty-source protection...'

DO $validation$
DECLARE
    v_source_count BIGINT;
    v_cache_count BIGINT;
    v_preserved_cache_count BIGINT;
    v_preserved_checkpoint_count BIGINT;
    v_failed_run_count BIGINT;
    v_failed_table_result_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_source_count
    FROM central_repository.appointment_type_reference;

    IF v_source_count <> 0 THEN
        RAISE EXCEPTION
            'Expected an empty central source; found % rows',
            v_source_count;
    END IF;

    RAISE NOTICE
        'empty_source_precondition_assertion: passed';


    SELECT COUNT(*)
    INTO v_cache_count
    FROM facility_cache.appointment_type_reference;

    IF v_cache_count <> 1 THEN
        RAISE EXCEPTION
            'Expected one preserved cache record; found %',
            v_cache_count;
    END IF;


    SELECT COUNT(*)
    INTO v_preserved_cache_count
    FROM facility_cache.appointment_type_reference
    WHERE appointment_type_code = 'ROUTINE'
      AND display_name = 'Routine Visit'
      AND description =
          'Previously synchronized cache record that must be preserved.'
      AND active_flag = TRUE
      AND effective_date = DATE '2026-01-01'
      AND expiration_date IS NULL
      AND source_updated_at =
          TIMESTAMPTZ '2026-07-22 00:01:00+00'
      AND source_version = 7
      AND sync_run_id =
          'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'
      AND synced_at =
          TIMESTAMPTZ '2026-07-22 00:15:00+00';

    IF v_preserved_cache_count <> 1 THEN
        RAISE EXCEPTION
            'The preexisting cache record was modified or removed';
    END IF;

    RAISE NOTICE
        'existing_cache_preservation_assertion: passed';


    /*
     * A failed full refresh must not advance or replace the last known
     * successful checkpoint.
     */
    SELECT COUNT(*)
    INTO v_preserved_checkpoint_count
    FROM sync_control.sync_checkpoint
    WHERE reference_domain = 'appointment_type'
      AND last_source_updated_at =
          TIMESTAMPTZ '2026-07-22 00:01:00+00'
      AND last_source_key = 'ROUTINE'
      AND last_successful_sync_run_id =
          'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee'
      AND updated_at =
          TIMESTAMPTZ '2026-07-22 00:15:00+00';

    IF v_preserved_checkpoint_count <> 1 THEN
        RAISE EXCEPTION
            'The previous successful checkpoint was modified';
    END IF;

    RAISE NOTICE
        'existing_checkpoint_preservation_assertion: passed';


    SELECT COUNT(*)
    INTO v_failed_run_count
    FROM sync_control.sync_run
    WHERE sync_run_id =
            'ffffffff-ffff-ffff-ffff-ffffffffffff'
      AND reference_domain = 'appointment_type'
      AND load_mode = 'full_refresh'
      AND run_status = 'failed'
      AND completed_at IS NOT NULL
      AND source_row_count = 0
      AND inserted_row_count = 0
      AND target_row_count = 1
      AND reconciliation_status = 'failed'
      AND error_message =
          'Source table is empty; full refresh aborted '
          'to protect the facility cache.';

    IF v_failed_run_count <> 1 THEN
        RAISE EXCEPTION
            'Failed synchronization-run evidence is incorrect';
    END IF;

    RAISE NOTICE
        'empty_source_run_failure_assertion: passed';


    SELECT COUNT(*)
    INTO v_failed_table_result_count
    FROM sync_control.sync_table_result
    WHERE sync_run_id =
            'ffffffff-ffff-ffff-ffff-ffffffffffff'
      AND source_table_name =
            'central_repository.appointment_type_reference'
      AND target_table_name =
            'facility_cache.appointment_type_reference'
      AND table_status = 'failed'
      AND completed_at IS NOT NULL
      AND source_row_count = 0
      AND inserted_row_count = 0
      AND target_row_count = 1
      AND reconciliation_status = 'failed'
      AND error_message =
          'Source table is empty; full refresh aborted '
          'to protect the facility cache.';

    IF v_failed_table_result_count <> 1 THEN
        RAISE EXCEPTION
            'Failed table-result evidence is incorrect';
    END IF;

    RAISE NOTICE
        'empty_source_table_failure_assertion: passed';
END;
$validation$;


\echo 'Observed preserved cache record:'

SELECT
    appointment_type_code,
    display_name,
    source_version,
    sync_run_id,
    synced_at
FROM facility_cache.appointment_type_reference;


\echo 'Observed preserved synchronization checkpoint:'

SELECT
    reference_domain,
    last_source_updated_at,
    last_source_key,
    last_successful_sync_run_id,
    updated_at
FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';


\echo 'Observed failed synchronization run:'

SELECT
    sync_run_id,
    run_status,
    source_row_count,
    inserted_row_count,
    target_row_count,
    reconciliation_status,
    error_message
FROM sync_control.sync_run
WHERE sync_run_id =
    'ffffffff-ffff-ffff-ffff-ffffffffffff';


\echo 'Observed failed table result:'

SELECT
    table_status,
    source_row_count,
    inserted_row_count,
    target_row_count,
    reconciliation_status,
    error_message
FROM sync_control.sync_table_result
WHERE sync_run_id =
    'ffffffff-ffff-ffff-ffff-ffffffffffff';


ROLLBACK;