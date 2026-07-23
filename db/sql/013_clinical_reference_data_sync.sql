CREATE SCHEMA IF NOT EXISTS central_repository;

CREATE SCHEMA IF NOT EXISTS facility_cache;

CREATE SCHEMA IF NOT EXISTS sync_control;


CREATE TABLE IF NOT EXISTS central_repository.appointment_type_reference (
    appointment_type_code TEXT PRIMARY KEY,

    display_name TEXT NOT NULL,

    description TEXT,

    active_flag BOOLEAN NOT NULL DEFAULT TRUE,

    effective_date DATE NOT NULL,

    expiration_date DATE,

    source_updated_at TIMESTAMPTZ NOT NULL,

    source_version BIGINT NOT NULL,

    CONSTRAINT chk_appointment_type_code_not_blank
        CHECK (BTRIM(appointment_type_code) <> ''),

    CONSTRAINT chk_appointment_type_display_name_not_blank
        CHECK (BTRIM(display_name) <> ''),

    CONSTRAINT chk_appointment_type_valid_date_range
        CHECK (
            expiration_date IS NULL
            OR expiration_date >= effective_date
        ),

    CONSTRAINT chk_appointment_type_source_version_positive
        CHECK (source_version > 0)
);

CREATE TABLE IF NOT EXISTS facility_cache.appointment_type_reference (
    appointment_type_code TEXT PRIMARY KEY,

    display_name TEXT NOT NULL,

    description TEXT,

    active_flag BOOLEAN NOT NULL,

    effective_date DATE NOT NULL,

    expiration_date DATE,

    source_updated_at TIMESTAMPTZ NOT NULL,

    source_version BIGINT NOT NULL,

    sync_run_id UUID NOT NULL,

    synced_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_cached_appointment_type_code_not_blank
        CHECK (BTRIM(appointment_type_code) <> ''),

    CONSTRAINT chk_cached_appointment_type_display_name_not_blank
        CHECK (BTRIM(display_name) <> ''),

    CONSTRAINT chk_cached_appointment_type_valid_date_range
        CHECK (
            expiration_date IS NULL
            OR expiration_date >= effective_date
        ),

    CONSTRAINT chk_cached_appointment_type_source_version_positive
        CHECK (source_version > 0)
);

CREATE TABLE IF NOT EXISTS sync_control.sync_run (
    sync_run_id UUID PRIMARY KEY,

    reference_domain TEXT NOT NULL,

    load_mode TEXT NOT NULL,

    run_status TEXT NOT NULL,

    processing_window_started_at TIMESTAMPTZ NOT NULL,

    processing_window_deadline_at TIMESTAMPTZ NOT NULL,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    source_row_count BIGINT,

    inserted_row_count BIGINT NOT NULL DEFAULT 0,

    updated_row_count BIGINT NOT NULL DEFAULT 0,

    deactivated_row_count BIGINT NOT NULL DEFAULT 0,

    rejected_row_count BIGINT NOT NULL DEFAULT 0,

    target_row_count BIGINT,

    reconciliation_status TEXT NOT NULL DEFAULT 'not_run',

    error_message TEXT,

    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_sync_run_reference_domain_not_blank
        CHECK (BTRIM(reference_domain) <> ''),

    CONSTRAINT chk_sync_run_load_mode
        CHECK (
            load_mode IN (
                'full_refresh',
                'incremental'
            )
        ),

    CONSTRAINT chk_sync_run_status
        CHECK (
            run_status IN (
                'started',
                'loading',
                'reconciling',
                'completed',
                'failed'
            )
        ),

    CONSTRAINT chk_sync_run_reconciliation_status
        CHECK (
            reconciliation_status IN (
                'not_run',
                'passed',
                'failed'
            )
        ),

    CONSTRAINT chk_sync_run_processing_window
        CHECK (
            processing_window_deadline_at
            > processing_window_started_at
        ),

    CONSTRAINT chk_sync_run_completion_time
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        ),

    CONSTRAINT chk_sync_run_source_row_count
        CHECK (
            source_row_count IS NULL
            OR source_row_count >= 0
        ),

    CONSTRAINT chk_sync_run_inserted_row_count
        CHECK (inserted_row_count >= 0),

    CONSTRAINT chk_sync_run_updated_row_count
        CHECK (updated_row_count >= 0),

    CONSTRAINT chk_sync_run_deactivated_row_count
        CHECK (deactivated_row_count >= 0),

    CONSTRAINT chk_sync_run_rejected_row_count
        CHECK (rejected_row_count >= 0),

    CONSTRAINT chk_sync_run_target_row_count
        CHECK (
            target_row_count IS NULL
            OR target_row_count >= 0
        )
);

DO $migration$
BEGIN
    IF NOT EXISTS (
        SELECT 1
        FROM pg_constraint
        WHERE conname = 'fk_cached_appointment_type_sync_run'
          AND conrelid =
              'facility_cache.appointment_type_reference'::regclass
    ) THEN
        ALTER TABLE facility_cache.appointment_type_reference
        ADD CONSTRAINT fk_cached_appointment_type_sync_run
        FOREIGN KEY (sync_run_id)
        REFERENCES sync_control.sync_run(sync_run_id);
    END IF;
END;
$migration$;

CREATE TABLE IF NOT EXISTS sync_control.sync_table_result (
    sync_table_result_id BIGSERIAL PRIMARY KEY,

    sync_run_id UUID NOT NULL
        REFERENCES sync_control.sync_run(sync_run_id),

    source_table_name TEXT NOT NULL,

    target_table_name TEXT NOT NULL,

    table_status TEXT NOT NULL,

    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    completed_at TIMESTAMPTZ,

    source_row_count BIGINT,

    inserted_row_count BIGINT NOT NULL DEFAULT 0,

    updated_row_count BIGINT NOT NULL DEFAULT 0,

    deactivated_row_count BIGINT NOT NULL DEFAULT 0,

    rejected_row_count BIGINT NOT NULL DEFAULT 0,

    target_row_count BIGINT,

    reconciliation_status TEXT NOT NULL DEFAULT 'not_run',

    error_message TEXT,

    CONSTRAINT uq_sync_table_result_run_source_target
        UNIQUE (
            sync_run_id,
            source_table_name,
            target_table_name
        ),

    CONSTRAINT chk_sync_table_result_source_not_blank
        CHECK (BTRIM(source_table_name) <> ''),

    CONSTRAINT chk_sync_table_result_target_not_blank
        CHECK (BTRIM(target_table_name) <> ''),

    CONSTRAINT chk_sync_table_result_status
        CHECK (
            table_status IN (
                'started',
                'loading',
                'reconciling',
                'completed',
                'failed'
            )
        ),

    CONSTRAINT chk_sync_table_result_reconciliation_status
        CHECK (
            reconciliation_status IN (
                'not_run',
                'passed',
                'failed'
            )
        ),

    CONSTRAINT chk_sync_table_result_completion_time
        CHECK (
            completed_at IS NULL
            OR completed_at >= started_at
        ),

    CONSTRAINT chk_sync_table_result_source_row_count
        CHECK (
            source_row_count IS NULL
            OR source_row_count >= 0
        ),

    CONSTRAINT chk_sync_table_result_inserted_row_count
        CHECK (inserted_row_count >= 0),

    CONSTRAINT chk_sync_table_result_updated_row_count
        CHECK (updated_row_count >= 0),

    CONSTRAINT chk_sync_table_result_deactivated_row_count
        CHECK (deactivated_row_count >= 0),

    CONSTRAINT chk_sync_table_result_rejected_row_count
        CHECK (rejected_row_count >= 0),

    CONSTRAINT chk_sync_table_result_target_row_count
        CHECK (
            target_row_count IS NULL
            OR target_row_count >= 0
        )
);

CREATE TABLE IF NOT EXISTS sync_control.sync_checkpoint (
    reference_domain TEXT PRIMARY KEY,

    last_source_updated_at TIMESTAMPTZ NOT NULL,

    last_source_key TEXT NOT NULL,

    last_successful_sync_run_id UUID NOT NULL
        REFERENCES sync_control.sync_run(sync_run_id),

    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT chk_sync_checkpoint_domain_not_blank
        CHECK (BTRIM(reference_domain) <> ''),

    CONSTRAINT chk_sync_checkpoint_source_key_not_blank
        CHECK (BTRIM(last_source_key) <> '')
);

CREATE INDEX IF NOT EXISTS idx_sync_table_result_sync_run_id
ON sync_control.sync_table_result (
    sync_run_id
);

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
     * Other sessions therefore see either the previously committed cache
     * or the newly committed cache, not a partially refreshed data set.
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

    v_completed_at := clock_timestamp();

    IF v_source_row_count = v_inserted_row_count
       AND v_source_row_count = v_target_row_count THEN

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