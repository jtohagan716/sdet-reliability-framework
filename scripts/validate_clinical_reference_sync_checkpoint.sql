\set ON_ERROR_STOP on

BEGIN;

\echo 'Creating a completed synchronization run...'

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
    '12121212-1212-1212-1212-121212121212',
    'appointment_type',
    'full_refresh',
    'completed',
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00',
    TIMESTAMPTZ '2026-07-23 00:10:00+00',
    TIMESTAMPTZ '2026-07-23 00:20:00+00',
    5,
    5,
    5,
    'passed'
);


\echo 'Creating one valid checkpoint...'

INSERT INTO sync_control.sync_checkpoint (
    reference_domain,
    last_source_updated_at,
    last_source_key,
    last_successful_sync_run_id,
    updated_at
)
VALUES (
    'appointment_type',
    TIMESTAMPTZ '2026-07-23 00:05:00+00',
    'URGENT',
    '12121212-1212-1212-1212-121212121212',
    TIMESTAMPTZ '2026-07-23 00:20:00+00'
);


DO $validation$
BEGIN
    BEGIN
        INSERT INTO sync_control.sync_checkpoint (
            reference_domain,
            last_source_updated_at,
            last_source_key,
            last_successful_sync_run_id
        )
        VALUES (
            'appointment_type',
            TIMESTAMPTZ '2026-07-23 00:06:00+00',
            'ANOTHER',
            '12121212-1212-1212-1212-121212121212'
        );

        RAISE EXCEPTION
            'Duplicate reference-domain checkpoint was accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'checkpoint_domain_uniqueness_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_checkpoint (
            reference_domain,
            last_source_updated_at,
            last_source_key,
            last_successful_sync_run_id
        )
        VALUES (
            '   ',
            TIMESTAMPTZ '2026-07-23 00:06:00+00',
            'BLANK_DOMAIN',
            '12121212-1212-1212-1212-121212121212'
        );

        RAISE EXCEPTION
            'Blank reference domain was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'checkpoint_domain_not_blank_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_checkpoint (
            reference_domain,
            last_source_updated_at,
            last_source_key,
            last_successful_sync_run_id
        )
        VALUES (
            'blank_key_test',
            TIMESTAMPTZ '2026-07-23 00:06:00+00',
            '   ',
            '12121212-1212-1212-1212-121212121212'
        );

        RAISE EXCEPTION
            'Blank source key was accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'checkpoint_source_key_not_blank_assertion: passed';
    END;


    BEGIN
        INSERT INTO sync_control.sync_checkpoint (
            reference_domain,
            last_source_updated_at,
            last_source_key,
            last_successful_sync_run_id
        )
        VALUES (
            'orphan_run_test',
            TIMESTAMPTZ '2026-07-23 00:06:00+00',
            'ORPHAN',
            '34343434-3434-3434-3434-343434343434'
        );

        RAISE EXCEPTION
            'Checkpoint with an orphan run identifier was accepted';
    EXCEPTION
        WHEN foreign_key_violation THEN
            RAISE NOTICE
                'checkpoint_sync_run_foreign_key_assertion: passed';
    END;
END;
$validation$;


\echo 'Observed valid checkpoint:'

SELECT
    reference_domain,
    last_source_updated_at,
    last_source_key,
    last_successful_sync_run_id,
    updated_at
FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';


\echo 'Verifying only one controlled checkpoint exists...'

SELECT COUNT(*) AS valid_checkpoint_count
FROM sync_control.sync_checkpoint
WHERE reference_domain IN (
    'appointment_type',
    'blank_key_test',
    'orphan_run_test'
);

ROLLBACK;