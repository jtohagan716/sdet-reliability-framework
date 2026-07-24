\set ON_ERROR_STOP on

BEGIN;

\echo 'Preparing missing-checkpoint incremental scenario...'

DELETE FROM facility_cache.appointment_type_reference;
DELETE FROM central_repository.appointment_type_reference;

DELETE FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';

DELETE FROM sync_control.sync_table_result
WHERE sync_run_id IN (
    '44444444-4444-4444-4444-444444444444',
    '55555555-5555-5555-5555-555555555555'
);

DELETE FROM sync_control.sync_run
WHERE sync_run_id IN (
    '44444444-4444-4444-4444-444444444444',
    '55555555-5555-5555-5555-555555555555'
);


\echo 'Creating a previously successful cache run...'

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
    updated_row_count,
    target_row_count,
    reconciliation_status
)
VALUES (
    '44444444-4444-4444-4444-444444444444',
    'appointment_type',
    'full_refresh',
    'completed',
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00',
    TIMESTAMPTZ '2026-07-23 00:10:00+00',
    TIMESTAMPTZ '2026-07-23 00:15:00+00',
    2,
    2,
    0,
    2,
    'passed'
);


\echo 'Creating a valid existing facility cache...'

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
VALUES
    (
        'ROUTINE',
        'Routine Visit',
        'Previously synchronized routine appointment.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:00+00',
        1,
        '44444444-4444-4444-4444-444444444444',
        TIMESTAMPTZ '2026-07-23 00:15:00+00'
    ),
    (
        'TELEHEALTH',
        'Telehealth Visit',
        'Previously synchronized telehealth appointment.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        1,
        '44444444-4444-4444-4444-444444444444',
        TIMESTAMPTZ '2026-07-23 00:15:00+00'
    );


\echo 'Creating source changes that must not be processed...'

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
        'Previously synchronized routine appointment.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:00+00',
        1
    ),
    (
        'TELEHEALTH',
        'Updated Telehealth Visit',
        'Source value that must not overwrite the cache.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:03:00+00',
        2
    ),
    (
        'URGENT',
        'Urgent Visit',
        'New source row that must not be inserted.',
        TRUE,
        DATE '2026-07-23',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:04:00+00',
        1
    );


\echo 'Executing incremental synchronization without a checkpoint...'

CALL sync_control.incremental_sync_appointment_type_reference (
    '55555555-5555-5555-5555-555555555555',
    TIMESTAMPTZ '2026-07-23 01:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00'
);


\echo 'Validating safe failure behavior...'

DO $validation$
DECLARE
    v_source_count BIGINT;
    v_checkpoint_count BIGINT;
    v_cache_count BIGINT;
    v_preserved_cache_count BIGINT;
    v_new_cache_count BIGINT;
    v_failed_run_count BIGINT;
    v_failed_table_result_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_source_count
    FROM central_repository.appointment_type_reference;

    IF v_source_count <> 3 THEN
        RAISE EXCEPTION
            'Expected three source rows; found %',
            v_source_count;
    END IF;

    RAISE NOTICE
        'missing_checkpoint_source_precondition_assertion: passed';


    SELECT COUNT(*)
    INTO v_checkpoint_count
    FROM sync_control.sync_checkpoint
    WHERE reference_domain = 'appointment_type';

    IF v_checkpoint_count <> 0 THEN
        RAISE EXCEPTION
            'Expected no appointment-type checkpoint';
    END IF;

    RAISE NOTICE
        'missing_checkpoint_precondition_assertion: passed';


    SELECT COUNT(*)
    INTO v_cache_count
    FROM facility_cache.appointment_type_reference;

    IF v_cache_count <> 2 THEN
        RAISE EXCEPTION
            'Expected two preserved cache rows; found %',
            v_cache_count;
    END IF;


    SELECT COUNT(*)
    INTO v_preserved_cache_count
    FROM facility_cache.appointment_type_reference
    WHERE (
            appointment_type_code = 'ROUTINE'
        AND display_name = 'Routine Visit'
        AND source_version = 1
        AND sync_run_id =
            '44444444-4444-4444-4444-444444444444'
    )
    OR (
            appointment_type_code = 'TELEHEALTH'
        AND display_name = 'Telehealth Visit'
        AND description =
            'Previously synchronized telehealth appointment.'
        AND source_updated_at =
            TIMESTAMPTZ '2026-07-23 00:02:00+00'
        AND source_version = 1
        AND sync_run_id =
            '44444444-4444-4444-4444-444444444444'
    );

    IF v_preserved_cache_count <> 2 THEN
        RAISE EXCEPTION
            'Existing cache rows were modified';
    END IF;

    RAISE NOTICE
        'missing_checkpoint_cache_preservation_assertion: passed';


    SELECT COUNT(*)
    INTO v_new_cache_count
    FROM facility_cache.appointment_type_reference
    WHERE appointment_type_code = 'URGENT';

    IF v_new_cache_count <> 0 THEN
        RAISE EXCEPTION
            'New source row was inserted without a checkpoint';
    END IF;

    RAISE NOTICE
        'missing_checkpoint_insert_prevention_assertion: passed';


    SELECT COUNT(*)
    INTO v_checkpoint_count
    FROM sync_control.sync_checkpoint
    WHERE reference_domain = 'appointment_type';

    IF v_checkpoint_count <> 0 THEN
        RAISE EXCEPTION
            'A checkpoint was created by the failed run';
    END IF;

    RAISE NOTICE
        'missing_checkpoint_creation_prevention_assertion: passed';


    SELECT COUNT(*)
    INTO v_failed_run_count
    FROM sync_control.sync_run
    WHERE sync_run_id =
            '55555555-5555-5555-5555-555555555555'
      AND reference_domain = 'appointment_type'
      AND load_mode = 'incremental'
      AND run_status = 'failed'
      AND completed_at IS NOT NULL
      AND source_row_count = 0
      AND inserted_row_count = 0
      AND updated_row_count = 0
      AND target_row_count = 2
      AND reconciliation_status = 'failed'
      AND error_message =
          'No successful checkpoint exists; run a full refresh '
          'before incremental synchronization.';

    IF v_failed_run_count <> 1 THEN
        RAISE EXCEPTION
            'Missing-checkpoint run evidence is incorrect';
    END IF;

    RAISE NOTICE
        'missing_checkpoint_run_failure_assertion: passed';


    SELECT COUNT(*)
    INTO v_failed_table_result_count
    FROM sync_control.sync_table_result
    WHERE sync_run_id =
            '55555555-5555-5555-5555-555555555555'
      AND source_table_name =
            'central_repository.appointment_type_reference'
      AND target_table_name =
            'facility_cache.appointment_type_reference'
      AND table_status = 'failed'
      AND completed_at IS NOT NULL
      AND source_row_count = 0
      AND inserted_row_count = 0
      AND updated_row_count = 0
      AND target_row_count = 2
      AND reconciliation_status = 'failed'
      AND error_message =
          'No successful checkpoint exists; run a full refresh '
          'before incremental synchronization.';

    IF v_failed_table_result_count <> 1 THEN
        RAISE EXCEPTION
            'Missing-checkpoint table evidence is incorrect';
    END IF;

    RAISE NOTICE
        'missing_checkpoint_table_failure_assertion: passed';
END;
$validation$;


\echo 'Observed preserved facility cache:'

SELECT
    appointment_type_code,
    display_name,
    source_version,
    sync_run_id
FROM facility_cache.appointment_type_reference
ORDER BY appointment_type_code;


\echo 'Observed failed incremental run:'

SELECT
    sync_run_id,
    load_mode,
    run_status,
    source_row_count,
    inserted_row_count,
    updated_row_count,
    target_row_count,
    reconciliation_status,
    error_message
FROM sync_control.sync_run
WHERE sync_run_id =
    '55555555-5555-5555-5555-555555555555';


ROLLBACK;