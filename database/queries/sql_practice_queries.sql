-- SQL practice and validation queries for the synthetic PostgreSQL schema.
-- These queries support database validation, join review, and future performance experiments.

-- 1. Inner join: patients with completed encounters.
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    e.encounter_id,
    e.encounter_date,
    e.status AS encounter_status
FROM patients p
JOIN encounters e
    ON p.patient_id = e.patient_id
WHERE e.status = 'completed'
ORDER BY p.patient_id, e.encounter_date DESC;

-- 2. Left join: all patients, including patients with no encounters.
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    e.encounter_id,
    e.encounter_date
FROM patients p
LEFT JOIN encounters e
    ON p.patient_id = e.patient_id
ORDER BY p.patient_id, e.encounter_date DESC;

-- 3. Anti-join pattern: patients with no encounters.
SELECT
    p.patient_id,
    p.first_name,
    p.last_name
FROM patients p
LEFT JOIN encounters e
    ON p.patient_id = e.patient_id
WHERE e.encounter_id IS NULL
ORDER BY p.patient_id;

-- 4. Multiple joins: encounter details with patient, provider, and facility.
SELECT
    e.encounter_id,
    e.encounter_date,
    p.first_name,
    p.last_name,
    pr.provider_name,
    pr.specialty,
    f.facility_name,
    f.region
FROM encounters e
JOIN patients p
    ON e.patient_id = p.patient_id
JOIN providers pr
    ON e.provider_id = pr.provider_id
JOIN facilities f
    ON e.facility_id = f.facility_id
ORDER BY e.encounter_date DESC;

-- 5. Many-to-many join: diagnoses by encounter.
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    e.encounter_id,
    d.diagnosis_code,
    d.diagnosis_name,
    d.category
FROM patients p
JOIN encounters e
    ON p.patient_id = e.patient_id
JOIN encounter_diagnoses ed
    ON e.encounter_id = ed.encounter_id
JOIN diagnoses d
    ON ed.diagnosis_code = d.diagnosis_code
ORDER BY p.patient_id, e.encounter_id, d.diagnosis_code;

-- 6. Aggregation: encounter counts by facility.
SELECT
    f.facility_name,
    COUNT(e.encounter_id) AS encounter_count
FROM facilities f
LEFT JOIN encounters e
    ON f.facility_id = e.facility_id
GROUP BY f.facility_name
ORDER BY encounter_count DESC, f.facility_name;

-- 7. Common Table Expression and window function: most recent encounter per patient.
WITH ranked_encounters AS (
    SELECT
        e.*,
        ROW_NUMBER() OVER (
            PARTITION BY e.patient_id
            ORDER BY e.encounter_date DESC
        ) AS row_number
    FROM encounters e
)
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    re.encounter_id,
    re.encounter_date,
    re.encounter_type,
    re.status
FROM patients p
LEFT JOIN ranked_encounters re
    ON p.patient_id = re.patient_id
   AND re.row_number = 1
ORDER BY p.patient_id;

-- 8. Cross join / Cartesian join: all patient and facility combinations.
-- This is useful when intentional, but dangerous if accidental on large tables.
SELECT
    p.patient_id,
    p.first_name,
    p.last_name,
    f.facility_id,
    f.facility_name
FROM patients p
CROSS JOIN facilities f
ORDER BY p.patient_id, f.facility_id;

-- 9. Future performance query candidate.
-- This can later be tested with EXPLAIN ANALYZE and indexes.
SELECT
    e.facility_id,
    e.encounter_date,
    e.status
FROM encounters e
WHERE e.facility_id = 2
  AND e.encounter_date >= '2026-04-01'
ORDER BY e.encounter_date DESC;
