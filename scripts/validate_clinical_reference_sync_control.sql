\set ON_ERROR_STOP on

BEGIN;

\echo 'Creating one valid synchronization run...'

INSERT INTO sync_control.sync_run (
    sync_run_id,
    reference_domain,
    load_mode,
    run_status,
    processing_window_started_at,
    processing_window_deadline_at,
    started_at
)
VALUES (
    '11111111-1111-1111-1111-111111111111',
    'appointment_type',
    'full_refresh',
    'loading',
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00',
    TIMESTAMPTZ '2026-07-23 00:15:00+00'
);

\echo 'Creating one valid cache record linked to the run...'

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
    'Standard scheduled appointment',
    TRUE,
    DATE '2026-01-01',
    NULL,
    TIMESTAMPTZ '2026-07-22 22:00:00+00',
    1,
    '11111111-1111-1111-1111-111111111111',
    TIMESTAMPTZ '2026-07-23 00:20:00+00'
);


DO $validation$
BEGIN
    BEGIN
        INSERT INTO sync_control.sync_run (
            sync_run_id,
            reference_domain,
            load_mode,
            run_status,
            processing_window_started_at,
            processing_window_deadline_at,
            started_at
        )
        VALUES (
            '22222222-2222-2222-2222-222222222222',
            'appointment_type',
            'delta',
            'started',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            TIMESTAMPTZ '2026-07-23 05:00:00+00',
            TIMESTAMPTZ '2026-07-23 00:10:00+00'
        );

        RAISE EXCEPTION
            'Invalid load mode was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'load_mode_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_run (
            sync_run_id,
            reference_domain,
            load_mode,
            run_status,
            processing_window_started_at,
            processing_window_deadline_at,
            started_at
        )
        VALUES (
            '33333333-3333-3333-3333-333333333333',
            'appointment_type',
            'full_refresh',
            'unknown',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            TIMESTAMPTZ '2026-07-23 05:00:00+00',
            TIMESTAMPTZ '2026-07-23 00:10:00+00'
        );

        RAISE EXCEPTION
            'Invalid run status was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'run_status_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_run (
            sync_run_id,
            reference_domain,
            load_mode,
            run_status,
            processing_window_started_at,
            processing_window_deadline_at,
            started_at
        )
        VALUES (
            '44444444-4444-4444-4444-444444444444',
            'appointment_type',
            'full_refresh',
            'started',
            TIMESTAMPTZ '2026-07-23 05:00:00+00',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            TIMESTAMPTZ '2026-07-23 00:10:00+00'
        );

        RAISE EXCEPTION
            'Invalid processing window was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'processing_window_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_run (
            sync_run_id,
            reference_domain,
            load_mode,
            run_status,
            processing_window_started_at,
            processing_window_deadline_at,
            started_at,
            inserted_row_count
        )
        VALUES (
            '55555555-5555-5555-5555-555555555555',
            'appointment_type',
            'full_refresh',
            'started',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            TIMESTAMPTZ '2026-07-23 05:00:00+00',
            TIMESTAMPTZ '2026-07-23 00:10:00+00',
            -1
        );

        RAISE EXCEPTION
            'Negative inserted-row count was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'nonnegative_row_count_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_run (
            sync_run_id,
            reference_domain,
            load_mode,
            run_status,
            processing_window_started_at,
            processing_window_deadline_at,
            started_at,
            completed_at
        )
        VALUES (
            '66666666-6666-6666-6666-666666666666',
            'appointment_type',
            'full_refresh',
            'completed',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            TIMESTAMPTZ '2026-07-23 05:00:00+00',
            TIMESTAMPTZ '2026-07-23 01:00:00+00',
            TIMESTAMPTZ '2026-07-23 00:30:00+00'
        );

        RAISE EXCEPTION
            'Completion before start was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'completion_time_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO facility_cache.appointment_type_reference (
            appointment_type_code,
            display_name,
            active_flag,
            effective_date,
            source_updated_at,
            source_version,
            sync_run_id
        )
        VALUES (
            'ORPHAN',
            'Orphan Cache Record',
            TRUE,
            DATE '2026-01-01',
            TIMESTAMPTZ '2026-07-22 22:00:00+00',
            1,
            '99999999-9999-9999-9999-999999999999'
        );

        RAISE EXCEPTION
            'Cache record without a synchronization run was accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'cache_sync_run_foreign_key_assertion: passed';
    END;
END;
$validation$;


\echo 'Valid synchronization run:'

SELECT
    sync_run_id,
    reference_domain,
    load_mode,
    run_status,
    processing_window_started_at,
    processing_window_deadline_at
FROM sync_control.sync_run
WHERE sync_run_id =
    '11111111-1111-1111-1111-111111111111';


\echo 'Valid linked cache record:'

SELECT
    appointment_type_code,
    display_name,
    source_version,
    sync_run_id
FROM facility_cache.appointment_type_reference
WHERE appointment_type_code = 'ROUTINE';


\echo 'Verifying only the valid controlled records exist...'

SELECT COUNT(*) AS valid_sync_run_count
FROM sync_control.sync_run
WHERE sync_run_id IN (
    '11111111-1111-1111-1111-111111111111',
    '22222222-2222-2222-2222-222222222222',
    '33333333-3333-3333-3333-333333333333',
    '44444444-4444-4444-4444-444444444444',
    '55555555-5555-5555-5555-555555555555',
    '66666666-6666-6666-6666-666666666666'
);

SELECT COUNT(*) AS valid_cache_record_count
FROM facility_cache.appointment_type_reference
WHERE appointment_type_code IN (
    'ROUTINE',
    'ORPHAN'
);

ROLLBACK;