-- PostgreSQL schema for synthetic database-backed reliability validation.
-- This database is for local/project validation only.
-- No real patient data, protected health information, or personally identifiable information is used.

BEGIN;

DROP TABLE IF EXISTS lab_results CASCADE;
DROP TABLE IF EXISTS lab_orders CASCADE;
DROP TABLE IF EXISTS encounter_diagnoses CASCADE;
DROP TABLE IF EXISTS encounters CASCADE;
DROP TABLE IF EXISTS diagnoses CASCADE;
DROP TABLE IF EXISTS providers CASCADE;
DROP TABLE IF EXISTS facilities CASCADE;
DROP TABLE IF EXISTS patients CASCADE;

CREATE TABLE patients (
    patient_id INTEGER PRIMARY KEY,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    date_of_birth DATE NOT NULL,
    status VARCHAR(20) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT chk_patients_status
        CHECK (status IN ('active', 'inactive'))
);

CREATE TABLE facilities (
    facility_id INTEGER PRIMARY KEY,
    facility_name VARCHAR(100) NOT NULL,
    facility_type VARCHAR(50) NOT NULL,
    region VARCHAR(50) NOT NULL
);

CREATE TABLE providers (
    provider_id INTEGER PRIMARY KEY,
    provider_name VARCHAR(100) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    facility_id INTEGER NOT NULL,
    CONSTRAINT fk_providers_facility
        FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id)
);

CREATE TABLE diagnoses (
    diagnosis_code VARCHAR(20) PRIMARY KEY,
    diagnosis_name VARCHAR(150) NOT NULL,
    category VARCHAR(100) NOT NULL
);

CREATE TABLE encounters (
    encounter_id INTEGER PRIMARY KEY,
    patient_id INTEGER NOT NULL,
    provider_id INTEGER NOT NULL,
    facility_id INTEGER NOT NULL,
    encounter_date DATE NOT NULL,
    encounter_type VARCHAR(50) NOT NULL,
    status VARCHAR(20) NOT NULL,
    CONSTRAINT fk_encounters_patient
        FOREIGN KEY (patient_id)
        REFERENCES patients(patient_id),
    CONSTRAINT fk_encounters_provider
        FOREIGN KEY (provider_id)
        REFERENCES providers(provider_id),
    CONSTRAINT fk_encounters_facility
        FOREIGN KEY (facility_id)
        REFERENCES facilities(facility_id),
    CONSTRAINT chk_encounters_status
        CHECK (status IN ('scheduled', 'completed', 'cancelled'))
);

CREATE TABLE encounter_diagnoses (
    encounter_id INTEGER NOT NULL,
    diagnosis_code VARCHAR(20) NOT NULL,
    PRIMARY KEY (encounter_id, diagnosis_code),
    CONSTRAINT fk_encounter_diagnoses_encounter
        FOREIGN KEY (encounter_id)
        REFERENCES encounters(encounter_id),
    CONSTRAINT fk_encounter_diagnoses_diagnosis
        FOREIGN KEY (diagnosis_code)
        REFERENCES diagnoses(diagnosis_code)
);

CREATE TABLE lab_orders (
    lab_order_id INTEGER PRIMARY KEY,
    encounter_id INTEGER NOT NULL,
    order_name VARCHAR(100) NOT NULL,
    ordered_at TIMESTAMPTZ NOT NULL,
    status VARCHAR(20) NOT NULL,
    CONSTRAINT fk_lab_orders_encounter
        FOREIGN KEY (encounter_id)
        REFERENCES encounters(encounter_id),
    CONSTRAINT chk_lab_orders_status
        CHECK (status IN ('ordered', 'completed', 'cancelled'))
);

CREATE TABLE lab_results (
    lab_result_id INTEGER PRIMARY KEY,
    lab_order_id INTEGER NOT NULL,
    result_name VARCHAR(100) NOT NULL,
    result_value VARCHAR(50) NOT NULL,
    result_unit VARCHAR(50),
    reference_range VARCHAR(100),
    result_status VARCHAR(20) NOT NULL,
    resulted_at TIMESTAMPTZ NOT NULL,
    CONSTRAINT fk_lab_results_order
        FOREIGN KEY (lab_order_id)
        REFERENCES lab_orders(lab_order_id),
    CONSTRAINT chk_lab_results_status
        CHECK (result_status IN ('pending', 'final', 'corrected'))
);

COMMIT;
