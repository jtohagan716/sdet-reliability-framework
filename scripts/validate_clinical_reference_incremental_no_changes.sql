\set ON_ERROR_STOP on

BEGIN;

\echo 'Preparing no-change incremental synchronization scenario...'

DELETE FROM facility_cache.appointment_type_reference;
DELETE FROM central_repository.appointment_type_reference;

DELETE FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';

DELETE FROM sync_control.sync_table_result
WHERE sync_run_id IN (
    '66666666-6666-6666-6666-666666666666',
    '77777777-7777-7777-7777-777777777777'
);

DELETE FROM sync_control.sync_run
WHERE sync_run_id IN (
    '66666666-6666-6666-6666-666666666666',
    '77777777-7777-7777-7777-777777777777'
);


\echo 'Creating the previous successful synchronization run...'

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
    '66666666-6666-6666-6666-666666666666',
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


\echo 'Creating the checkpoint at the latest source position...'

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
    '66666666-6666-6666-6666-666666666666',
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
        'Existing routine appointment.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:00+00',
        1,
        '66666666-6666-6666-6666-666666666666',
        TIMESTAMPTZ '2026-07-23 00:15:00+00'
    ),
    (
        'TELEHEALTH',
        'Telehealth Visit',
        'Existing telehealth appointment.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        1,
        '66666666-6666-6666-6666-666666666666',
        TIMESTAMPTZ '2026-07-23 00:15:00+00'
    );


\echo 'Creating an identical central source state...'

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
        'Existing routine appointment.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:00+00',
        1
    ),
    (
        'TELEHEALTH',
        'Telehealth Visit',
        'Existing telehealth appointment.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        1
    );


\echo 'Executing an incremental synchronization with no new changes...'

CALL sync_control.incremental_sync_appointment_type_reference (
    '77777777-7777-7777-7777-777777777777',
    TIMESTAMPTZ '2026-07-23 01:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00'
);


\echo 'Validating idempotent no-change behavior...'

DO $validation$
DECLARE
    v_cache_count BIGINT;
    v_preserved_cache_count BIGINT;
    v_current_run_cache_count BIGINT;
    v_checkpoint_count BIGINT;
    v_run_count BIGINT;
    v_table_result_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_cache_count
    FROM facility_cache.appointment_type_reference;

    IF v_cache_count <> 2 THEN
        RAISE EXCEPTION
            'Expected two unchanged cache rows; found %',
            v_cache_count;
    END IF;


    SELECT COUNT(*)
    INTO v_preserved_cache_count
    FROM facility_cache.appointment_type_reference
    WHERE sync_run_id =
          '66666666-6666-6666-6666-666666666666'
      AND synced_at =
          TIMESTAMPTZ '2026-07-23 00:15:00+00';

    IF v_preserved_cache_count <> 2 THEN
        RAISE EXCEPTION
            'No-change run unexpectedly rewrote cache rows';
    END IF;

    RAISE NOTICE
        'no_change_cache_preservation_assertion: passed';


    SELECT COUNT(*)
    INTO v_current_run_cache_count
    FROM facility_cache.appointment_type_reference
    WHERE sync_run_id =
          '77777777-7777-7777-7777-777777777777';

    IF v_current_run_cache_count <> 0 THEN
        RAISE EXCEPTION
            'No-change run claimed ownership of cache rows';
    END IF;

    RAISE NOTICE
        'no_change_write_prevention_assertion: passed';


    SELECT COUNT(*)
    INTO v_checkpoint_count
    FROM sync_control.sync_checkpoint
    WHERE reference_domain = 'appointment_type'
      AND last_source_updated_at =
          TIMESTAMPTZ '2026-07-23 00:02:00+00'
      AND last_source_key = 'TELEHEALTH'
      AND last_successful_sync_run_id =
          '66666666-6666-6666-6666-666666666666'
      AND updated_at =
          TIMESTAMPTZ '2026-07-23 00:15:00+00';

    IF v_checkpoint_count <> 1 THEN
        RAISE EXCEPTION
            'No-change run unexpectedly modified the checkpoint';
    END IF;

    RAISE NOTICE
        'no_change_checkpoint_preservation_assertion: passed';


    SELECT COUNT(*)
    INTO v_run_count
    FROM sync_control.sync_run
    WHERE sync_run_id =
            '77777777-7777-7777-7777-777777777777'
      AND load_mode = 'incremental'
      AND run_status = 'completed'
      AND completed_at IS NOT NULL
      AND source_row_count = 0
      AND inserted_row_count = 0
      AND updated_row_count = 0
      AND target_row_count = 2
      AND reconciliation_status = 'passed'
      AND error_message IS NULL;

    IF v_run_count <> 1 THEN
        RAISE EXCEPTION
            'No-change synchronization-run evidence is incorrect';
    END IF;

    RAISE NOTICE
        'no_change_run_evidence_assertion: passed';


    SELECT COUNT(*)
    INTO v_table_result_count
    FROM sync_control.sync_table_result
    WHERE sync_run_id =
            '77777777-7777-7777-7777-777777777777'
      AND table_status = 'completed'
      AND completed_at IS NOT NULL
      AND source_row_count = 0
      AND inserted_row_count = 0
      AND updated_row_count = 0
      AND target_row_count = 2
      AND reconciliation_status = 'passed'
      AND error_message IS NULL;

    IF v_table_result_count <> 1 THEN
        RAISE EXCEPTION
            'No-change table-result evidence is incorrect';
    END IF;

    RAISE NOTICE
        'no_change_table_evidence_assertion: passed';
END;
$validation$;


\echo 'Observed unchanged facility cache:'

SELECT
    appointment_type_code,
    display_name,
    source_version,
    sync_run_id,
    synced_at
FROM facility_cache.appointment_type_reference
ORDER BY appointment_type_code;


\echo 'Observed unchanged checkpoint:'

SELECT
    reference_domain,
    last_source_updated_at,
    last_source_key,
    last_successful_sync_run_id,
    updated_at
FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';


\echo 'Observed successful no-change run:'

SELECT
    sync_run_id,
    load_mode,
    run_status,
    source_row_count,
    inserted_row_count,
    updated_row_count,
    target_row_count,
    reconciliation_status
FROM sync_control.sync_run
WHERE sync_run_id =
    '77777777-7777-7777-7777-777777777777';


ROLLBACK;