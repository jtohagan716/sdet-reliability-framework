\set ON_ERROR_STOP on

BEGIN;

\echo 'Preparing deterministic incremental synchronization scenario...'

DELETE FROM facility_cache.appointment_type_reference;
DELETE FROM central_repository.appointment_type_reference;

DELETE FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';

DELETE FROM sync_control.sync_table_result
WHERE sync_run_id IN (
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333'
);

DELETE FROM sync_control.sync_run
WHERE sync_run_id IN (
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333'
);


\echo 'Creating the previous successful full-refresh run...'

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
    '22222222-2222-2222-2222-222222222222',
    'appointment_type',
    'full_refresh',
    'completed',
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00',
    TIMESTAMPTZ '2026-07-23 00:10:00+00',
    TIMESTAMPTZ '2026-07-23 00:15:00+00',
    3,
    3,
    0,
    3,
    'passed'
);


\echo 'Creating the existing compound checkpoint...'

INSERT INTO sync_control.sync_checkpoint (
    reference_domain,
    last_source_updated_at,
    last_source_key,
    last_successful_sync_run_id,
    updated_at
)
VALUES (
    'appointment_type',
    TIMESTAMPTZ '2026-07-23 00:02:00+00',
    'TELEHEALTH',
    '22222222-2222-2222-2222-222222222222',
    TIMESTAMPTZ '2026-07-23 00:15:00+00'
);


\echo 'Creating the existing facility cache...'

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
        'Existing record before the checkpoint.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:00+00',
        1,
        '22222222-2222-2222-2222-222222222222',
        TIMESTAMPTZ '2026-07-23 00:15:00+00'
    ),
    (
        'TELEHEALTH',
        'Telehealth Visit',
        'Existing record exactly at the checkpoint.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        1,
        '22222222-2222-2222-2222-222222222222',
        TIMESTAMPTZ '2026-07-23 00:15:00+00'
    ),
    (
        'FOLLOWUP',
        'Follow-up Visit',
        'Old cache value that must be updated.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:30+00',
        1,
        '22222222-2222-2222-2222-222222222222',
        TIMESTAMPTZ '2026-07-23 00:15:00+00'
    );


\echo 'Creating the current central source state...'

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
        'Existing record before the checkpoint.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:00+00',
        1
    ),
    (
        'TELEHEALTH',
        'Telehealth Visit',
        'Existing record exactly at the checkpoint.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        1
    ),
    (
        'URGENT',
        'Urgent Visit',
        'New row sharing the checkpoint timestamp with a higher key.',
        TRUE,
        DATE '2026-07-23',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        1
    ),
    (
        'FOLLOWUP',
        'Post-treatment Follow-up',
        'Updated cache value from the central repository.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:03:00+00',
        2
    );


\echo 'Executing incremental synchronization...'

CALL sync_control.incremental_sync_appointment_type_reference (
    '33333333-3333-3333-3333-333333333333',
    TIMESTAMPTZ '2026-07-23 01:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00'
);


\echo 'Validating incremental synchronization behavior...'

DO $validation$
DECLARE
    v_target_count BIGINT;
    v_inserted_count BIGINT;
    v_updated_count BIGINT;
    v_unchanged_count BIGINT;
    v_checkpoint_count BIGINT;
    v_run_count BIGINT;
    v_table_result_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_target_count
    FROM facility_cache.appointment_type_reference;

    IF v_target_count <> 4 THEN
        RAISE EXCEPTION
            'Expected four cache rows; found %',
            v_target_count;
    END IF;

    RAISE NOTICE
        'incremental_target_count_assertion: passed';


    SELECT COUNT(*)
    INTO v_inserted_count
    FROM facility_cache.appointment_type_reference
    WHERE appointment_type_code = 'URGENT'
      AND display_name = 'Urgent Visit'
      AND source_updated_at =
          TIMESTAMPTZ '2026-07-23 00:02:00+00'
      AND source_version = 1
      AND sync_run_id =
          '33333333-3333-3333-3333-333333333333';

    IF v_inserted_count <> 1 THEN
        RAISE EXCEPTION
            'New URGENT cache row was not inserted correctly';
    END IF;

    RAISE NOTICE
        'incremental_insert_assertion: passed';


    SELECT COUNT(*)
    INTO v_updated_count
    FROM facility_cache.appointment_type_reference
    WHERE appointment_type_code = 'FOLLOWUP'
      AND display_name = 'Post-treatment Follow-up'
      AND description =
          'Updated cache value from the central repository.'
      AND source_updated_at =
          TIMESTAMPTZ '2026-07-23 00:03:00+00'
      AND source_version = 2
      AND sync_run_id =
          '33333333-3333-3333-3333-333333333333';

    IF v_updated_count <> 1 THEN
        RAISE EXCEPTION
            'Existing FOLLOWUP cache row was not updated correctly';
    END IF;

    RAISE NOTICE
        'incremental_update_assertion: passed';


    SELECT COUNT(*)
    INTO v_unchanged_count
    FROM facility_cache.appointment_type_reference
    WHERE appointment_type_code IN (
        'ROUTINE',
        'TELEHEALTH'
    )
      AND sync_run_id =
          '22222222-2222-2222-2222-222222222222';

    IF v_unchanged_count <> 2 THEN
        RAISE EXCEPTION
            'Rows at or before the checkpoint were unexpectedly modified';
    END IF;

    RAISE NOTICE
        'incremental_unchanged_rows_assertion: passed';


    SELECT COUNT(*)
    INTO v_checkpoint_count
    FROM sync_control.sync_checkpoint
    WHERE reference_domain = 'appointment_type'
      AND last_source_updated_at =
          TIMESTAMPTZ '2026-07-23 00:03:00+00'
      AND last_source_key = 'FOLLOWUP'
      AND last_successful_sync_run_id =
          '33333333-3333-3333-3333-333333333333';

    IF v_checkpoint_count <> 1 THEN
        RAISE EXCEPTION
            'Incremental checkpoint was not advanced correctly';
    END IF;

    RAISE NOTICE
        'incremental_checkpoint_advancement_assertion: passed';


    SELECT COUNT(*)
    INTO v_run_count
    FROM sync_control.sync_run
    WHERE sync_run_id =
            '33333333-3333-3333-3333-333333333333'
      AND load_mode = 'incremental'
      AND run_status = 'completed'
      AND source_row_count = 2
      AND inserted_row_count = 1
      AND updated_row_count = 1
      AND target_row_count = 4
      AND reconciliation_status = 'passed'
      AND error_message IS NULL;

    IF v_run_count <> 1 THEN
        RAISE EXCEPTION
            'Incremental synchronization-run evidence is incorrect';
    END IF;

    RAISE NOTICE
        'incremental_run_evidence_assertion: passed';


    SELECT COUNT(*)
    INTO v_table_result_count
    FROM sync_control.sync_table_result
    WHERE sync_run_id =
            '33333333-3333-3333-3333-333333333333'
      AND table_status = 'completed'
      AND source_row_count = 2
      AND inserted_row_count = 1
      AND updated_row_count = 1
      AND target_row_count = 4
      AND reconciliation_status = 'passed'
      AND error_message IS NULL;

    IF v_table_result_count <> 1 THEN
        RAISE EXCEPTION
            'Incremental table-result evidence is incorrect';
    END IF;

    RAISE NOTICE
        'incremental_table_evidence_assertion: passed';
END;
$validation$;


\echo 'Observed facility-cache state:'

SELECT
    appointment_type_code,
    display_name,
    source_version,
    sync_run_id
FROM facility_cache.appointment_type_reference
ORDER BY appointment_type_code;


\echo 'Observed incremental run evidence:'

SELECT
    load_mode,
    run_status,
    source_row_count,
    inserted_row_count,
    updated_row_count,
    target_row_count,
    reconciliation_status
FROM sync_control.sync_run
WHERE sync_run_id =
    '33333333-3333-3333-3333-333333333333';


\echo 'Observed advanced checkpoint:'

SELECT
    reference_domain,
    last_source_updated_at,
    last_source_key,
    last_successful_sync_run_id
FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';


ROLLBACK;