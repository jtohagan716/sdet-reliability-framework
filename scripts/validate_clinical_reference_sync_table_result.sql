\set ON_ERROR_STOP on

BEGIN;

\echo 'Creating a valid parent synchronization run...'

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
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'appointment_type',
    'full_refresh',
    'loading',
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00',
    TIMESTAMPTZ '2026-07-23 00:10:00+00'
);


\echo 'Creating one valid table result...'

INSERT INTO sync_control.sync_table_result (
    sync_run_id,
    source_table_name,
    target_table_name,
    table_status,
    started_at,
    completed_at,
    source_row_count,
    inserted_row_count,
    updated_row_count,
    deactivated_row_count,
    rejected_row_count,
    target_row_count,
    reconciliation_status
)
VALUES (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'central_repository.appointment_type_reference',
    'facility_cache.appointment_type_reference',
    'completed',
    TIMESTAMPTZ '2026-07-23 00:15:00+00',
    TIMESTAMPTZ '2026-07-23 00:20:00+00',
    5,
    5,
    0,
    0,
    0,
    5,
    'passed'
);


DO $validation$
BEGIN
    BEGIN
        INSERT INTO sync_control.sync_table_result (
            sync_run_id,
            source_table_name,
            target_table_name,
            table_status
        )
        VALUES (
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'central_repository.appointment_type_reference',
            'facility_cache.appointment_type_reference',
            'started'
        );

        RAISE EXCEPTION
            'Duplicate table result was incorrectly accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'unique_table_result_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_table_result (
            sync_run_id,
            source_table_name,
            target_table_name,
            table_status
        )
        VALUES (
            'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb',
            'central_repository.appointment_type_reference',
            'facility_cache.appointment_type_reference',
            'started'
        );

        RAISE EXCEPTION
            'Orphan table result was incorrectly accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'sync_run_foreign_key_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_table_result (
            sync_run_id,
            source_table_name,
            target_table_name,
            table_status
        )
        VALUES (
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            '   ',
            'facility_cache.blank_source_test',
            'started'
        );

        RAISE EXCEPTION
            'Blank source table name was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'source_table_not_blank_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_table_result (
            sync_run_id,
            source_table_name,
            target_table_name,
            table_status
        )
        VALUES (
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'central_repository.blank_target_test',
            '   ',
            'started'
        );

        RAISE EXCEPTION
            'Blank target table name was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'target_table_not_blank_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_table_result (
            sync_run_id,
            source_table_name,
            target_table_name,
            table_status
        )
        VALUES (
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'central_repository.invalid_status_test',
            'facility_cache.invalid_status_test',
            'unknown'
        );

        RAISE EXCEPTION
            'Invalid table status was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'table_status_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_table_result (
            sync_run_id,
            source_table_name,
            target_table_name,
            table_status,
            inserted_row_count
        )
        VALUES (
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'central_repository.negative_count_test',
            'facility_cache.negative_count_test',
            'loading',
            -1
        );

        RAISE EXCEPTION
            'Negative inserted-row count was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'table_result_nonnegative_count_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_table_result (
            sync_run_id,
            source_table_name,
            target_table_name,
            table_status,
            reconciliation_status
        )
        VALUES (
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'central_repository.invalid_reconciliation_test',
            'facility_cache.invalid_reconciliation_test',
            'reconciling',
            'unknown'
        );

        RAISE EXCEPTION
            'Invalid reconciliation status was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'reconciliation_status_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_table_result (
            sync_run_id,
            source_table_name,
            target_table_name,
            table_status,
            started_at,
            completed_at
        )
        VALUES (
            'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
            'central_repository.invalid_time_test',
            'facility_cache.invalid_time_test',
            'completed',
            TIMESTAMPTZ '2026-07-23 01:00:00+00',
            TIMESTAMPTZ '2026-07-23 00:30:00+00'
        );

        RAISE EXCEPTION
            'Completion before start was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'table_result_completion_time_assertion: passed';
    END;
END;
$validation$;


\echo 'Valid table result:'

SELECT
    sync_run_id,
    source_table_name,
    target_table_name,
    table_status,
    source_row_count,
    inserted_row_count,
    target_row_count,
    reconciliation_status
FROM sync_control.sync_table_result
WHERE sync_run_id =
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa';


\echo 'Verifying only one controlled table result exists...'

SELECT COUNT(*) AS valid_table_result_count
FROM sync_control.sync_table_result
WHERE sync_run_id IN (
    'aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa',
    'bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb'
);

ROLLBACK;