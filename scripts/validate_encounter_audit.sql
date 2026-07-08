-- validate_encounter_audit.sql
-- Purpose:
-- Validate PostgreSQL encounter audit trigger behavior.
-- This runs inside a transaction and rolls back test data.

BEGIN;

SET LOCAL app.changed_by = 'audit_validation_test';
SET LOCAL app.change_source = 'manual_sql_validation';

CREATE TEMP TABLE audit_validation_target (
    encounter_id INTEGER NOT NULL
) ON COMMIT DROP;

WITH refs AS (
    SELECT
        COALESCE((SELECT MAX(encounter_id) FROM encounters), 0) + 1 AS encounter_id,
        (SELECT MIN(patient_id) FROM patients) AS patient_id,
        (SELECT MIN(provider_id) FROM providers) AS provider_id,
        (SELECT MIN(facility_id) FROM facilities) AS facility_id
),
inserted_encounter AS (
    INSERT INTO encounters (
        encounter_id,
        patient_id,
        provider_id,
        facility_id,
        encounter_date,
        encounter_type,
        status
    )
    SELECT
        refs.encounter_id,
        refs.patient_id,
        refs.provider_id,
        refs.facility_id,
        DATE '2026-07-08',
        'primary_care',
        'scheduled'
    FROM refs
    RETURNING encounter_id
)
INSERT INTO audit_validation_target (
    encounter_id
)
SELECT encounter_id
FROM inserted_encounter;

UPDATE encounters e
SET status = 'completed'
FROM audit_validation_target t
WHERE e.encounter_id = t.encounter_id;

SELECT
    a.audit_id,
    a.encounter_id,
    a.operation_type,
    a.old_status,
    a.new_status,
    a.old_encounter_date,
    a.new_encounter_date,
    a.old_encounter_type,
    a.new_encounter_type,
    a.changed_by,
    a.change_source
FROM encounter_audit a
JOIN audit_validation_target t
    ON a.encounter_id = t.encounter_id
ORDER BY a.audit_id;

ROLLBACK;