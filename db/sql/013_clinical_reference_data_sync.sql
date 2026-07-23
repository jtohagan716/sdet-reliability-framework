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