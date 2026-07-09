BEGIN;

\echo 'Creating a synthetic FHIR reference validation evidence run...'

INSERT INTO fhir_validation_runs (
    run_name,
    scenario_name,
    run_status,
    details
)
VALUES (
    'manual_fhir_reference_validation_evidence',
    'synthetic_fhir_reference_integrity',
    'started',
    jsonb_build_object(
        'data_scope', 'synthetic_fhir_fixtures',
        'real_patient_data_used', false,
        'purpose', 'Prove valid references and expected broken reference detection are queryable in PostgreSQL'
    )
)
RETURNING validation_run_id \gset

\echo 'Recording resource checks...'

INSERT INTO fhir_resource_checks (
    validation_run_id,
    resource_type,
    resource_id,
    resource_reference,
    check_name,
    check_status,
    details
)
VALUES
(
    :validation_run_id,
    'Patient',
    'example-patient-001',
    'Patient/example-patient-001',
    'resource_exists',
    'passed',
    jsonb_build_object('fixture', 'test_data/fhir/patient-example.json')
),
(
    :validation_run_id,
    'Encounter',
    'example-encounter-001',
    'Encounter/example-encounter-001',
    'resource_exists',
    'passed',
    jsonb_build_object('fixture', 'test_data/fhir/encounter-example.json')
),
(
    :validation_run_id,
    'Observation',
    'example-observation-001',
    'Observation/example-observation-001',
    'resource_exists',
    'passed',
    jsonb_build_object('fixture', 'test_data/fhir/observation-example.json')
),
(
    :validation_run_id,
    'DiagnosticReport',
    'example-diagnosticreport-001',
    'DiagnosticReport/example-diagnosticreport-001',
    'resource_exists',
    'passed',
    jsonb_build_object('fixture', 'test_data/fhir/diagnosticreport-example.json')
),
(
    :validation_run_id,
    'DiagnosticReport',
    'example-diagnosticreport-broken-001',
    'DiagnosticReport/example-diagnosticreport-broken-001',
    'resource_exists',
    'passed',
    jsonb_build_object('fixture', 'test_data/fhir/invalid/diagnosticreport-broken-observation-reference.json')
);

\echo 'Recording valid reference checks...'

INSERT INTO fhir_reference_checks (
    validation_run_id,
    source_reference,
    declared_reference,
    target_exists,
    check_status,
    details
)
VALUES
(
    :validation_run_id,
    'Encounter/example-encounter-001',
    'Patient/example-patient-001',
    true,
    'passed',
    jsonb_build_object('field', 'Encounter.subject.reference')
),
(
    :validation_run_id,
    'Observation/example-observation-001',
    'Patient/example-patient-001',
    true,
    'passed',
    jsonb_build_object('field', 'Observation.subject.reference')
),
(
    :validation_run_id,
    'Observation/example-observation-001',
    'Encounter/example-encounter-001',
    true,
    'passed',
    jsonb_build_object('field', 'Observation.encounter.reference')
),
(
    :validation_run_id,
    'DiagnosticReport/example-diagnosticreport-001',
    'Patient/example-patient-001',
    true,
    'passed',
    jsonb_build_object('field', 'DiagnosticReport.subject.reference')
),
(
    :validation_run_id,
    'DiagnosticReport/example-diagnosticreport-001',
    'Encounter/example-encounter-001',
    true,
    'passed',
    jsonb_build_object('field', 'DiagnosticReport.encounter.reference')
),
(
    :validation_run_id,
    'DiagnosticReport/example-diagnosticreport-001',
    'Observation/example-observation-001',
    true,
    'passed',
    jsonb_build_object('field', 'DiagnosticReport.result.reference')
);

\echo 'Recording intentionally broken reference check...'

INSERT INTO fhir_reference_checks (
    validation_run_id,
    source_reference,
    declared_reference,
    target_exists,
    check_status,
    details
)
VALUES
(
    :validation_run_id,
    'DiagnosticReport/example-diagnosticreport-broken-001',
    'Observation/example-observation-missing-001',
    false,
    'failed',
    jsonb_build_object(
        'field', 'DiagnosticReport.result.reference',
        'expected_negative_fixture', true,
        'reason', 'Referenced Observation is intentionally missing from the synthetic fixture set'
    )
);

UPDATE fhir_validation_runs
SET
    run_status = 'completed',
    completed_at = NOW(),
    details = details || jsonb_build_object(
        'expected_reference_failures', 1,
        'validation_result', 'completed_with_expected_negative_finding'
    )
WHERE validation_run_id = :validation_run_id;

\echo 'FHIR validation run summary:'

SELECT
    validation_run_id,
    run_name,
    scenario_name,
    run_status,
    details
FROM fhir_validation_runs
WHERE validation_run_id = :validation_run_id;

\echo 'FHIR resource check summary:'

SELECT
    resource_type,
    resource_reference,
    check_name,
    check_status
FROM fhir_resource_checks
WHERE validation_run_id = :validation_run_id
ORDER BY resource_check_id;

\echo 'FHIR reference check summary:'

SELECT
    source_reference,
    declared_reference,
    target_exists,
    check_status,
    details
FROM fhir_reference_checks
WHERE validation_run_id = :validation_run_id
ORDER BY reference_check_id;

\echo 'Expected missing reference finding:'

SELECT
    source_reference,
    declared_reference AS missing_reference,
    check_status,
    details
FROM fhir_reference_checks
WHERE validation_run_id = :validation_run_id
  AND check_status = 'failed';

ROLLBACK;