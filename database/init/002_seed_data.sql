-- Synthetic seed data for PostgreSQL database-backed reliability validation.
-- Data is intentionally fictional and deterministic.

BEGIN;

INSERT INTO patients (patient_id, first_name, last_name, date_of_birth, status)
VALUES
    (1001, 'Alex', 'Morgan', '1980-04-12', 'active'),
    (1002, 'Jordan', 'Lee', '1975-09-30', 'inactive'),
    (1003, 'Taylor', 'Kim', '1990-01-18', 'active'),
    (1004, 'Casey', 'Rivera', '1968-11-02', 'active');

INSERT INTO facilities (facility_id, facility_name, facility_type, region)
VALUES
    (1, 'North Clinic', 'outpatient', 'northeast'),
    (2, 'West Medical Center', 'hospital', 'west'),
    (3, 'South Community Care', 'outpatient', 'south');

INSERT INTO providers (provider_id, provider_name, specialty, facility_id)
VALUES
    (501, 'Dr. Avery Stone', 'Family Medicine', 1),
    (502, 'Dr. Morgan Patel', 'Internal Medicine', 2),
    (503, 'Dr. Riley Brooks', 'Pulmonology', 2),
    (504, 'Dr. Harper Chen', 'Endocrinology', 3);

INSERT INTO diagnoses (diagnosis_code, diagnosis_name, category)
VALUES
    ('I10', 'Hypertension', 'cardiovascular'),
    ('E11.9', 'Type 2 diabetes mellitus without complications', 'endocrine'),
    ('J45.909', 'Asthma, unspecified', 'respiratory'),
    ('Z00.00', 'General adult medical examination', 'preventive');

INSERT INTO encounters (
    encounter_id,
    patient_id,
    provider_id,
    facility_id,
    encounter_date,
    encounter_type,
    status
)
VALUES
    (9001, 1001, 501, 1, '2026-06-15', 'office_visit', 'completed'),
    (9002, 1001, 502, 2, '2026-05-10', 'follow_up', 'completed'),
    (9003, 1002, 504, 3, '2026-05-20', 'office_visit', 'completed'),
    (9004, 1004, 503, 2, '2026-04-02', 'specialist_visit', 'completed'),
    (9005, 1004, 501, 1, '2026-07-20', 'office_visit', 'scheduled');

INSERT INTO encounter_diagnoses (encounter_id, diagnosis_code)
VALUES
    (9001, 'I10'),
    (9001, 'Z00.00'),
    (9002, 'I10'),
    (9003, 'E11.9'),
    (9004, 'J45.909');

INSERT INTO lab_orders (lab_order_id, encounter_id, order_name, ordered_at, status)
VALUES
    (7001, 9001, 'Basic Metabolic Panel', '2026-06-15 09:15:00-04', 'completed'),
    (7002, 9003, 'Hemoglobin A1C', '2026-05-20 10:30:00-04', 'completed'),
    (7003, 9004, 'Pulmonary Function Panel', '2026-04-02 14:00:00-04', 'completed');

INSERT INTO lab_results (
    lab_result_id,
    lab_order_id,
    result_name,
    result_value,
    result_unit,
    reference_range,
    result_status,
    resulted_at
)
VALUES
    (8001, 7001, 'Sodium', '140', 'mmol/L', '135-145', 'final', '2026-06-15 12:00:00-04'),
    (8002, 7001, 'Potassium', '4.2', 'mmol/L', '3.5-5.1', 'final', '2026-06-15 12:00:00-04'),
    (8003, 7002, 'A1C', '7.1', '%', '<5.7', 'final', '2026-05-20 13:45:00-04'),
    (8004, 7003, 'FEV1', '82', '% predicted', '80-120', 'final', '2026-04-02 16:10:00-04');

COMMIT;
