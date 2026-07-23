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