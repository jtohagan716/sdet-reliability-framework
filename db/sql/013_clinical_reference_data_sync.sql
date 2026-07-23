CREATE OR REPLACE PROCEDURE
sync_control.full_refresh_appointment_type_reference (
    p_sync_run_id UUID,
    p_processing_window_started_at TIMESTAMPTZ,
    p_processing_window_deadline_at TIMESTAMPTZ
)
LANGUAGE plpgsql
AS $procedure$
DECLARE
    v_started_at TIMESTAMPTZ := clock_timestamp();
    v_completed_at TIMESTAMPTZ;
    v_cache_synced_at TIMESTAMPTZ;

    v_source_row_count BIGINT;
    v_inserted_row_count BIGINT;
    v_target_row_count BIGINT;

    v_last_source_updated_at TIMESTAMPTZ;
    v_last_source_key TEXT;
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
        p_sync_run_id,
        'appointment_type',
        'full_refresh',
        'loading',
        p_processing_window_started_at,
        p_processing_window_deadline_at,
        v_started_at
    );

    INSERT INTO sync_control.sync_table_result (
        sync_run_id,
        source_table_name,
        target_table_name,
        table_status,
        started_at
    )
    VALUES (
        p_sync_run_id,
        'central_repository.appointment_type_reference',
        'facility_cache.appointment_type_reference',
        'loading',
        v_started_at
    );

    SELECT COUNT(*)
    INTO v_source_row_count
    FROM central_repository.appointment_type_reference;

    /*
     * Protect the facility cache from an accidental destructive refresh.
     *
     * An empty source may represent an upstream failure rather than a
     * legitimate empty reference-data domain. The existing cache remains
     * untouched and the run is recorded as failed.
     */
    IF v_source_row_count = 0 THEN
        SELECT COUNT(*)
        INTO v_target_row_count
        FROM facility_cache.appointment_type_reference;

        v_completed_at := clock_timestamp();

        UPDATE sync_control.sync_table_result
        SET
            table_status = 'failed',
            completed_at = v_completed_at,
            source_row_count = 0,
            target_row_count = v_target_row_count,
            reconciliation_status = 'failed',
            error_message =
                'Source table is empty; full refresh aborted '
                'to protect the facility cache.'
        WHERE sync_run_id = p_sync_run_id
          AND source_table_name =
              'central_repository.appointment_type_reference'
          AND target_table_name =
              'facility_cache.appointment_type_reference';

        UPDATE sync_control.sync_run
        SET
            run_status = 'failed',
            completed_at = v_completed_at,
            source_row_count = 0,
            target_row_count = v_target_row_count,
            reconciliation_status = 'failed',
            error_message =
                'Source table is empty; full refresh aborted '
                'to protect the facility cache.'
        WHERE sync_run_id = p_sync_run_id;

        RETURN;
    END IF;

    /*
     * DELETE and INSERT occur in the same database transaction.
     *
     * Other sessions see either the previously committed cache or the
     * newly committed cache, not a partially refreshed data set.
     */
    DELETE FROM facility_cache.appointment_type_reference;

    v_cache_synced_at := clock_timestamp();

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
    SELECT
        appointment_type_code,
        display_name,
        description,
        active_flag,
        effective_date,
        expiration_date,
        source_updated_at,
        source_version,
        p_sync_run_id,
        v_cache_synced_at
    FROM central_repository.appointment_type_reference;

    GET DIAGNOSTICS
        v_inserted_row_count = ROW_COUNT;

    SELECT COUNT(*)
    INTO v_target_row_count
    FROM facility_cache.appointment_type_reference;

    /*
     * Capture the final deterministic source position.
     *
     * The source key resolves ties when multiple records have the same
     * source_updated_at value.
     */
    SELECT
        source_updated_at,
        appointment_type_code
    INTO
        v_last_source_updated_at,
        v_last_source_key
    FROM central_repository.appointment_type_reference
    ORDER BY
        source_updated_at DESC,
        appointment_type_code DESC
    LIMIT 1;

    v_completed_at := clock_timestamp();

    IF v_source_row_count = v_inserted_row_count
       AND v_source_row_count = v_target_row_count THEN

        /*
         * Advance the checkpoint only after reconciliation succeeds.
         */
        INSERT INTO sync_control.sync_checkpoint (
            reference_domain,
            last_source_updated_at,
            last_source_key,
            last_successful_sync_run_id,
            updated_at
        )
        VALUES (
            'appointment_type',
            v_last_source_updated_at,
            v_last_source_key,
            p_sync_run_id,
            v_completed_at
        )
        ON CONFLICT (reference_domain)
        DO UPDATE
        SET
            last_source_updated_at =
                EXCLUDED.last_source_updated_at,
            last_source_key =
                EXCLUDED.last_source_key,
            last_successful_sync_run_id =
                EXCLUDED.last_successful_sync_run_id,
            updated_at =
                EXCLUDED.updated_at;

        UPDATE sync_control.sync_table_result
        SET
            table_status = 'completed',
            completed_at = v_completed_at,
            source_row_count = v_source_row_count,
            inserted_row_count = v_inserted_row_count,
            target_row_count = v_target_row_count,
            reconciliation_status = 'passed'
        WHERE sync_run_id = p_sync_run_id
          AND source_table_name =
              'central_repository.appointment_type_reference'
          AND target_table_name =
              'facility_cache.appointment_type_reference';

        UPDATE sync_control.sync_run
        SET
            run_status = 'completed',
            completed_at = v_completed_at,
            source_row_count = v_source_row_count,
            inserted_row_count = v_inserted_row_count,
            target_row_count = v_target_row_count,
            reconciliation_status = 'passed'
        WHERE sync_run_id = p_sync_run_id;

    ELSE
        UPDATE sync_control.sync_table_result
        SET
            table_status = 'failed',
            completed_at = v_completed_at,
            source_row_count = v_source_row_count,
            inserted_row_count = v_inserted_row_count,
            target_row_count = v_target_row_count,
            reconciliation_status = 'failed',
            error_message =
                'Source, inserted, and target row counts '
                'did not reconcile.'
        WHERE sync_run_id = p_sync_run_id
          AND source_table_name =
              'central_repository.appointment_type_reference'
          AND target_table_name =
              'facility_cache.appointment_type_reference';

        UPDATE sync_control.sync_run
        SET
            run_status = 'failed',
            completed_at = v_completed_at,
            source_row_count = v_source_row_count,
            inserted_row_count = v_inserted_row_count,
            target_row_count = v_target_row_count,
            reconciliation_status = 'failed',
            error_message =
                'Source, inserted, and target row counts '
                'did not reconcile.'
        WHERE sync_run_id = p_sync_run_id;
    END IF;
END;
$procedure$;