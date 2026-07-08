-- 004_encounter_audit_logic.sql
-- Purpose:
-- Add PostgreSQL stored audit logic for encounter inserts, updates, and deletes.

CREATE TABLE IF NOT EXISTS encounter_audit (
    audit_id BIGSERIAL PRIMARY KEY,

    encounter_id INTEGER NOT NULL,
    patient_id INTEGER,
    provider_id INTEGER,
    facility_id INTEGER,

    operation_type TEXT NOT NULL CHECK (operation_type IN ('INSERT', 'UPDATE', 'DELETE')),

    old_encounter_date DATE,
    new_encounter_date DATE,

    old_encounter_type VARCHAR,
    new_encounter_type VARCHAR,

    old_status VARCHAR,
    new_status VARCHAR,

    old_patient_id INTEGER,
    new_patient_id INTEGER,

    old_provider_id INTEGER,
    new_provider_id INTEGER,

    old_facility_id INTEGER,
    new_facility_id INTEGER,

    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    changed_by TEXT NOT NULL DEFAULT COALESCE(NULLIF(current_setting('app.changed_by', true), ''), current_user),
    change_source TEXT NOT NULL DEFAULT COALESCE(NULLIF(current_setting('app.change_source', true), ''), 'database'),

    -- Future OpenTelemetry correlation fields.
    -- These remain NULL until the API starts setting request trace context.
    trace_id TEXT,
    span_id TEXT,
    request_id TEXT,
    request_method TEXT,
    request_path TEXT,
    service_name TEXT
);


CREATE OR REPLACE FUNCTION write_encounter_audit(
    p_encounter_id INTEGER,
    p_patient_id INTEGER,
    p_provider_id INTEGER,
    p_facility_id INTEGER,
    p_operation_type TEXT,

    p_old_encounter_date DATE,
    p_new_encounter_date DATE,

    p_old_encounter_type VARCHAR,
    p_new_encounter_type VARCHAR,

    p_old_status VARCHAR,
    p_new_status VARCHAR,

    p_old_patient_id INTEGER,
    p_new_patient_id INTEGER,

    p_old_provider_id INTEGER,
    p_new_provider_id INTEGER,

    p_old_facility_id INTEGER,
    p_new_facility_id INTEGER
)
RETURNS VOID
LANGUAGE plpgsql
AS $$
BEGIN
    INSERT INTO encounter_audit (
        encounter_id,
        patient_id,
        provider_id,
        facility_id,
        operation_type,

        old_encounter_date,
        new_encounter_date,

        old_encounter_type,
        new_encounter_type,

        old_status,
        new_status,

        old_patient_id,
        new_patient_id,

        old_provider_id,
        new_provider_id,

        old_facility_id,
        new_facility_id,

        trace_id,
        span_id,
        request_id,
        request_method,
        request_path,
        service_name
    )
    VALUES (
        p_encounter_id,
        p_patient_id,
        p_provider_id,
        p_facility_id,
        p_operation_type,

        p_old_encounter_date,
        p_new_encounter_date,

        p_old_encounter_type,
        p_new_encounter_type,

        p_old_status,
        p_new_status,

        p_old_patient_id,
        p_new_patient_id,

        p_old_provider_id,
        p_new_provider_id,

        p_old_facility_id,
        p_new_facility_id,

        NULLIF(current_setting('app.trace_id', true), ''),
        NULLIF(current_setting('app.span_id', true), ''),
        NULLIF(current_setting('app.request_id', true), ''),
        NULLIF(current_setting('app.request_method', true), ''),
        NULLIF(current_setting('app.request_path', true), ''),
        NULLIF(current_setting('app.service_name', true), '')
    );
END;
$$;


CREATE OR REPLACE FUNCTION audit_encounter_changes()
RETURNS TRIGGER
LANGUAGE plpgsql
AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        PERFORM write_encounter_audit(
            NEW.encounter_id,
            NEW.patient_id,
            NEW.provider_id,
            NEW.facility_id,
            'INSERT',

            NULL,
            NEW.encounter_date,

            NULL,
            NEW.encounter_type,

            NULL,
            NEW.status,

            NULL,
            NEW.patient_id,

            NULL,
            NEW.provider_id,

            NULL,
            NEW.facility_id
        );

        RETURN NEW;
    END IF;


    IF TG_OP = 'UPDATE' THEN
        IF OLD.patient_id IS DISTINCT FROM NEW.patient_id
           OR OLD.provider_id IS DISTINCT FROM NEW.provider_id
           OR OLD.facility_id IS DISTINCT FROM NEW.facility_id
           OR OLD.encounter_date IS DISTINCT FROM NEW.encounter_date
           OR OLD.encounter_type IS DISTINCT FROM NEW.encounter_type
           OR OLD.status IS DISTINCT FROM NEW.status THEN

            PERFORM write_encounter_audit(
                NEW.encounter_id,
                NEW.patient_id,
                NEW.provider_id,
                NEW.facility_id,
                'UPDATE',

                OLD.encounter_date,
                NEW.encounter_date,

                OLD.encounter_type,
                NEW.encounter_type,

                OLD.status,
                NEW.status,

                OLD.patient_id,
                NEW.patient_id,

                OLD.provider_id,
                NEW.provider_id,

                OLD.facility_id,
                NEW.facility_id
            );
        END IF;

        RETURN NEW;
    END IF;


    IF TG_OP = 'DELETE' THEN
        PERFORM write_encounter_audit(
            OLD.encounter_id,
            OLD.patient_id,
            OLD.provider_id,
            OLD.facility_id,
            'DELETE',

            OLD.encounter_date,
            NULL,

            OLD.encounter_type,
            NULL,

            OLD.status,
            NULL,

            OLD.patient_id,
            NULL,

            OLD.provider_id,
            NULL,

            OLD.facility_id,
            NULL
        );

        RETURN OLD;
    END IF;

    RETURN NULL;
END;
$$;


DROP TRIGGER IF EXISTS trg_audit_encounter_changes ON encounters;

CREATE TRIGGER trg_audit_encounter_changes
AFTER INSERT OR UPDATE OR DELETE ON encounters
FOR EACH ROW
EXECUTE FUNCTION audit_encounter_changes();