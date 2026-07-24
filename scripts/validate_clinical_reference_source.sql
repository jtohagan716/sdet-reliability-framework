\set ON_ERROR_STOP on

BEGIN;

\echo 'Inserting one valid appointment type...'

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
VALUES (
    'ROUTINE',
    'Routine Visit',
    'Standard scheduled appointment',
    TRUE,
    DATE '2026-01-01',
    NULL,
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    1
);

\echo 'Valid source record:'

SELECT
    appointment_type_code,
    display_name,
    active_flag,
    effective_date,
    expiration_date,
    source_version
FROM central_repository.appointment_type_reference
WHERE appointment_type_code = 'ROUTINE';


DO $validation$
BEGIN
    BEGIN
        INSERT INTO central_repository.appointment_type_reference (
            appointment_type_code,
            display_name,
            active_flag,
            effective_date,
            source_updated_at,
            source_version
        )
        VALUES (
            '   ',
            'Blank Code Example',
            TRUE,
            DATE '2026-01-01',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            1
        );

        RAISE EXCEPTION
            'Blank appointment type code was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'blank_code_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO central_repository.appointment_type_reference (
            appointment_type_code,
            display_name,
            active_flag,
            effective_date,
            source_updated_at,
            source_version
        )
        VALUES (
            'BLANK_NAME',
            '   ',
            TRUE,
            DATE '2026-01-01',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            1
        );

        RAISE EXCEPTION
            'Blank display name was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'blank_display_name_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO central_repository.appointment_type_reference (
            appointment_type_code,
            display_name,
            active_flag,
            effective_date,
            expiration_date,
            source_updated_at,
            source_version
        )
        VALUES (
            'BAD_DATES',
            'Invalid Date Range',
            TRUE,
            DATE '2026-12-31',
            DATE '2026-01-01',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            1
        );

        RAISE EXCEPTION
            'Invalid effective and expiration dates were incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'date_range_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO central_repository.appointment_type_reference (
            appointment_type_code,
            display_name,
            active_flag,
            effective_date,
            source_updated_at,
            source_version
        )
        VALUES (
            'BAD_VERSION',
            'Invalid Source Version',
            TRUE,
            DATE '2026-01-01',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            0
        );

        RAISE EXCEPTION
            'Nonpositive source version was incorrectly accepted';
    EXCEPTION
        WHEN check_violation THEN
            RAISE NOTICE
                'source_version_constraint_assertion: passed';
    END;


    BEGIN
        INSERT INTO central_repository.appointment_type_reference (
            appointment_type_code,
            display_name,
            active_flag,
            effective_date,
            source_updated_at,
            source_version
        )
        VALUES (
            'ROUTINE',
            'Duplicate Routine Visit',
            TRUE,
            DATE '2026-01-01',
            TIMESTAMPTZ '2026-07-23 00:00:00+00',
            2
        );

        RAISE EXCEPTION
            'Duplicate business key was incorrectly accepted';
    EXCEPTION
        WHEN unique_violation THEN
            RAISE NOTICE
                'duplicate_business_key_assertion: passed';
    END;
END;
$validation$;


\echo 'Verifying only the valid test record exists...'

SELECT
    COUNT(*) AS valid_test_record_count
FROM central_repository.appointment_type_reference
WHERE appointment_type_code IN (
    'ROUTINE',
    'BLANK_NAME',
    'BAD_DATES',
    'BAD_VERSION'
);

ROLLBACK;