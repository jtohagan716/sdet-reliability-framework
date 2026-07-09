CREATE TABLE IF NOT EXISTS fhir_validation_runs (
    validation_run_id BIGSERIAL PRIMARY KEY,
    run_name TEXT NOT NULL,
    scenario_name TEXT NOT NULL,
    run_status TEXT NOT NULL CHECK (
        run_status IN ('started', 'completed', 'failed')
    ),
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    completed_at TIMESTAMPTZ,
    details JSONB NOT NULL DEFAULT '{}'::jsonb
);

CREATE TABLE IF NOT EXISTS fhir_resource_checks (
    resource_check_id BIGSERIAL PRIMARY KEY,
    validation_run_id BIGINT NOT NULL REFERENCES fhir_validation_runs(validation_run_id) ON DELETE CASCADE,
    resource_type TEXT NOT NULL,
    resource_id TEXT NOT NULL,
    resource_reference TEXT NOT NULL,
    check_name TEXT NOT NULL,
    check_status TEXT NOT NULL CHECK (
        check_status IN ('passed', 'failed')
    ),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS fhir_reference_checks (
    reference_check_id BIGSERIAL PRIMARY KEY,
    validation_run_id BIGINT NOT NULL REFERENCES fhir_validation_runs(validation_run_id) ON DELETE CASCADE,
    source_reference TEXT NOT NULL,
    declared_reference TEXT NOT NULL,
    target_exists BOOLEAN NOT NULL,
    check_status TEXT NOT NULL CHECK (
        check_status IN ('passed', 'failed')
    ),
    details JSONB NOT NULL DEFAULT '{}'::jsonb,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_fhir_validation_runs_scenario_name
ON fhir_validation_runs (scenario_name);

CREATE INDEX IF NOT EXISTS idx_fhir_resource_checks_validation_run_id
ON fhir_resource_checks (validation_run_id);

CREATE INDEX IF NOT EXISTS idx_fhir_resource_checks_resource_reference
ON fhir_resource_checks (resource_reference);

CREATE INDEX IF NOT EXISTS idx_fhir_reference_checks_validation_run_id
ON fhir_reference_checks (validation_run_id);

CREATE INDEX IF NOT EXISTS idx_fhir_reference_checks_source_reference
ON fhir_reference_checks (source_reference);

CREATE INDEX IF NOT EXISTS idx_fhir_reference_checks_declared_reference
ON fhir_reference_checks (declared_reference);

CREATE INDEX IF NOT EXISTS idx_fhir_reference_checks_check_status
ON fhir_reference_checks (check_status);