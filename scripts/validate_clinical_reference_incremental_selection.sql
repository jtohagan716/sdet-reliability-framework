\set ON_ERROR_STOP on

BEGIN;

\echo 'Preparing deterministic incremental-selection scenario...'

DELETE FROM central_repository.appointment_type_reference;

DELETE FROM sync_control.sync_checkpoint
WHERE reference_domain = 'appointment_type';

DELETE FROM sync_control.sync_table_result
WHERE sync_run_id =
    '11111111-2222-3333-4444-555555555555';

DELETE FROM sync_control.sync_run
WHERE sync_run_id =
    '11111111-2222-3333-4444-555555555555';


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
    target_row_count,
    reconciliation_status
)
VALUES (
    '11111111-2222-3333-4444-555555555555',
    'appointment_type',
    'full_refresh',
    'completed',
    TIMESTAMPTZ '2026-07-23 00:00:00+00',
    TIMESTAMPTZ '2026-07-23 05:00:00+00',
    TIMESTAMPTZ '2026-07-23 00:10:00+00',
    TIMESTAMPTZ '2026-07-23 00:15:00+00',
    2,
    2,
    2,
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
    '11111111-2222-3333-4444-555555555555',
    TIMESTAMPTZ '2026-07-23 00:15:00+00'
);


\echo 'Creating deterministic source rows around the checkpoint...'

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
        'Record before the checkpoint timestamp.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:01:00+00',
        1
    ),
    (
        'TELEHEALTH',
        'Telehealth Visit',
        'Record exactly equal to the checkpoint.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        1
    ),
    (
        'URGENT',
        'Urgent Visit',
        'Record with the checkpoint timestamp but a higher key.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:02:00+00',
        2
    ),
    (
        'FOLLOWUP',
        'Follow-up Visit',
        'Record after the checkpoint timestamp.',
        TRUE,
        DATE '2026-01-01',
        NULL,
        TIMESTAMPTZ '2026-07-23 00:03:00+00',
        2
    );


\echo 'Validating deterministic incremental source selection...'

DO $validation$
DECLARE
    v_checkpoint_count BIGINT;
    v_selected_count BIGINT;
    v_selected_codes TEXT[];
    v_exact_checkpoint_selected_count BIGINT;
    v_prior_row_selected_count BIGINT;
    v_same_timestamp_higher_key_count BIGINT;
BEGIN
    SELECT COUNT(*)
    INTO v_checkpoint_count
    FROM sync_control.sync_checkpoint
    WHERE reference_domain = 'appointment_type'
      AND last_source_updated_at =
          TIMESTAMPTZ '2026-07-23 00:02:00+00'
      AND last_source_key = 'TELEHEALTH';

    IF v_checkpoint_count <> 1 THEN
        RAISE EXCEPTION
            'Expected exactly one deterministic checkpoint; found %',
            v_checkpoint_count;
    END IF;

    RAISE NOTICE
        'incremental_checkpoint_precondition_assertion: passed';


    SELECT
        COUNT(*),
        ARRAY_AGG(
            source.appointment_type_code
            ORDER BY
                source.source_updated_at,
                source.appointment_type_code
        )
    INTO
        v_selected_count,
        v_selected_codes
    FROM central_repository.appointment_type_reference AS source
    CROSS JOIN sync_control.sync_checkpoint AS checkpoint
    WHERE checkpoint.reference_domain = 'appointment_type'
      AND (
          source.source_updated_at,
          source.appointment_type_code
      ) > (
          checkpoint.last_source_updated_at,
          checkpoint.last_source_key
      );

    IF v_selected_count <> 2 THEN
        RAISE EXCEPTION
            'Expected two rows after the checkpoint; found %',
            v_selected_count;
    END IF;

    RAISE NOTICE
        'incremental_selection_count_assertion: passed';


    IF v_selected_codes <> ARRAY['URGENT', 'FOLLOWUP']::TEXT[] THEN
        RAISE EXCEPTION
            'Incremental selection order is incorrect; selected=%',
            v_selected_codes;
    END IF;

    RAISE NOTICE
        'incremental_selection_order_assertion: passed';


    SELECT COUNT(*)
    INTO v_exact_checkpoint_selected_count
    FROM central_repository.appointment_type_reference AS source
    CROSS JOIN sync_control.sync_checkpoint AS checkpoint
    WHERE checkpoint.reference_domain = 'appointment_type'
      AND source.appointment_type_code = 'TELEHEALTH'
      AND (
          source.source_updated_at,
          source.appointment_type_code
      ) > (
          checkpoint.last_source_updated_at,
          checkpoint.last_source_key
      );

    IF v_exact_checkpoint_selected_count <> 0 THEN
        RAISE EXCEPTION
            'The exact checkpoint row was selected again';
    END IF;

    RAISE NOTICE
        'exact_checkpoint_exclusion_assertion: passed';


    SELECT COUNT(*)
    INTO v_prior_row_selected_count
    FROM central_repository.appointment_type_reference AS source
    CROSS JOIN sync_control.sync_checkpoint AS checkpoint
    WHERE checkpoint.reference_domain = 'appointment_type'
      AND source.appointment_type_code = 'ROUTINE'
      AND (
          source.source_updated_at,
          source.appointment_type_code
      ) > (
          checkpoint.last_source_updated_at,
          checkpoint.last_source_key
      );

    IF v_prior_row_selected_count <> 0 THEN
        RAISE EXCEPTION
            'A source row before the checkpoint was selected';
    END IF;

    RAISE NOTICE
        'prior_source_row_exclusion_assertion: passed';


    SELECT COUNT(*)
    INTO v_same_timestamp_higher_key_count
    FROM central_repository.appointment_type_reference AS source
    CROSS JOIN sync_control.sync_checkpoint AS checkpoint
    WHERE checkpoint.reference_domain = 'appointment_type'
      AND source.appointment_type_code = 'URGENT'
      AND (
          source.source_updated_at,
          source.appointment_type_code
      ) > (
          checkpoint.last_source_updated_at,
          checkpoint.last_source_key
      );

    IF v_same_timestamp_higher_key_count <> 1 THEN
        RAISE EXCEPTION
            'The same-timestamp row with the higher key was not selected';
    END IF;

    RAISE NOTICE
        'compound_checkpoint_tie_breaker_assertion: passed';
END;
$validation$;


\echo 'Observed rows selected after the checkpoint:'

SELECT
    source.appointment_type_code,
    source.source_updated_at,
    source.source_version
FROM central_repository.appointment_type_reference AS source
CROSS JOIN sync_control.sync_checkpoint AS checkpoint
WHERE checkpoint.reference_domain = 'appointment_type'
  AND (
      source.source_updated_at,
      source.appointment_type_code
  ) > (
      checkpoint.last_source_updated_at,
      checkpoint.last_source_key
  )
ORDER BY
    source.source_updated_at,
    source.appointment_type_code;


ROLLBACK;