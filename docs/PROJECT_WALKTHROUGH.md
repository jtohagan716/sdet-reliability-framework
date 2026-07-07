# Project Walkthrough

## Overview

The SDET Reliability Framework is a practice-scale reliability validation project.

It demonstrates how a small service can be validated through automated tests, API checks, browser automation, accessibility smoke validation, PostgreSQL-backed data validation, performance baselines, lightweight load testing, dependency security review, and a repeatable release quality gate.

The project is intentionally synthetic.

It does not use real patient data, protected health information, personally identifiable information, credentials, secrets, or production data.

## Project Purpose

The purpose of this project is to demonstrate practical quality engineering and reliability validation behavior.

The framework focuses on questions that matter in real release work:

- Does the API return the expected contract?
- Does the system behave correctly for known success, not-found, and invalid-input paths?
- Are logs and request identifiers available for troubleshooting?
- Are metrics exposed for observability?
- Does the system have a known performance baseline?
- Can the system handle a lightweight weighted traffic mix?
- Are basic accessibility checks part of release readiness?
- Is PostgreSQL schema and seed data behavior deterministic?
- Does the API agree with direct database query results?
- Do database indexes support expected query behavior?
- Can validation detect a controlled business-rule defect?
- Are dependencies intentional and auditable?
- Are release checks repeatable instead of ad hoc?

## Architecture Summary

The project uses a small FastAPI service with synthetic patient lookup behavior.

The service can run with in-memory data or PostgreSQL-backed data depending on configuration.

Docker Compose provides a local validation stack that includes:

- FastAPI API service
- PostgreSQL database
- Prometheus
- Grafana

The validation layer includes:

- Pytest
- Postman/Newman
- Playwright
- axe-core for Playwright
- PowerShell validation scripts
- Python performance and load scripts
- Markdown release reports

## Core Application Endpoints

| Endpoint | Purpose |
|---|---|
| `/health` | Basic API health check |
| `/patients/1001` | Synthetic successful patient lookup |
| `/patients/1002` | Synthetic secondary patient lookup |
| `/patients/1003` | Additional synthetic patient lookup |
| `/patients/1004` | Synthetic patient used for database consistency and defect validation |
| `/patients/9999` | Expected not-found lookup |
| `/patients/abc` | Expected invalid-input response |
| `/metrics` | Prometheus metrics endpoint |
| `/patient-lookup` | Simple browser-facing page for accessibility validation |

## Synthetic Data Design

The project uses deterministic synthetic patient data.

Patient `1004` is especially important for database consistency validation.

The expected business rule is:

    last_visit should come from completed encounters only.

Patient `1004` includes both a completed encounter and a future scheduled encounter.

That makes the patient useful for validating whether the API correctly excludes scheduled encounters from the `last_visit` calculation.

## Validation Layers

### Pytest Regression Suite

Pytest validates backend behavior, helper functions, contract expectations, workflow logic, security helper behavior, and script behavior.

Run:

    python -m pytest

The current suite includes API, baseline, FHIR-oriented, payload, regression, performance, security, and workflow tests.

### Postman/Newman API Regression

Newman runs the Postman collection from the command line.

Run:

    npm run postman:test

This validates API behavior outside of Pytest and provides an additional command-line regression layer.

### Playwright Automation

Playwright validates browser-facing behavior and accessibility-oriented checks.

Run:

    npx playwright test

The project includes focused accessibility smoke validation and axe-core accessibility scan validation.

### Local Smoke Validation

The local smoke validation script checks Docker stack behavior, API health, synthetic patient behavior, Pytest, and Newman together.

Run:

    .\scripts\local_smoke_validation.ps1

This provides a practical local confidence check before release work.

### Performance Baseline

The performance baseline script captures local response-time and error-rate results for selected endpoints.

Run:

    python .\scripts\run_performance_baseline.py

The baseline provides a point of comparison for future changes.

### Lightweight Load Testing

The lightweight load test runs a weighted traffic mix with concurrency.

Run:

    python .\scripts\run_lightweight_load_test.py

The load test captures metrics such as throughput, average response time, p95, p99, and scenario-level outcomes.

### PostgreSQL Schema Validation

The PostgreSQL schema validation script confirms that the expected database structure and deterministic seed data are present.

Run:

    .\scripts\validate_postgresql_schema.ps1

This validates the relational foundation used by later API/database checks.

### PostgreSQL-Backed Patient Lookup Validation

The PostgreSQL-backed patient lookup validation confirms that the API can retrieve patient summary data from PostgreSQL while preserving the external API response contract.

Run:

    .\scripts\validate_postgresql_patient_lookup.ps1

### API-to-Database Consistency Validation

The API-to-database consistency validation compares API responses against direct PostgreSQL query results.

Run:

    .\scripts\validate_api_database_consistency.ps1

This validates that the API and database agree on key patient summary fields.

### PostgreSQL Query Plan and Index Validation

The query plan and index validation confirms that expected indexes exist and that PostgreSQL query plan evidence can be captured.

Run:

    .\scripts\validate_patient_lookup_query_plan.ps1

This supports backend reliability by making database access behavior visible.

### Controlled Defect Detection Validation

The controlled defect detection validation intentionally enables a known defect mode.

Run:

    .\scripts\validate_controlled_defect_detection.ps1

The script validates that the consistency checks catch the defect, then restores normal behavior.

This is useful because a validation framework should prove that it can detect meaningful defects, not only produce passing green-path results.

### Dependency Security Quality Gate

The dependency security validation script checks dependency health and audit posture.

Run:

    .\scripts\validate_dependency_security.ps1

The script treats the following as blocking:

- Python package dependency health
- Python vulnerability audit
- Node production/runtime audit

The full Node development/test-tooling audit is advisory.

Current Newman/Postman transitive findings are documented and monitored rather than force-fixed, because the available forced fix would apply a breaking Newman downgrade.

### Release Quality Gate

The release quality gate script runs the major validation checks and generates a release-readiness report.

Run:

    .\scripts\run_release_quality_gate.ps1

Optional controlled defect validation can be included with:

    .\scripts\run_release_quality_gate.ps1 -IncludeControlledDefectValidation

The default release gate does not include controlled defect validation because that script intentionally toggles defect behavior and recreates the API container.

## Release Progression

| Release | Capability |
|---|---|
| v0.2.0 | REST API validation and smoke testing |
| v0.3.0 | Diagnostic logging and request timing |
| v0.4.0 | Request identifier traceability |
| v0.5.0 | Prometheus metrics and observability signals |
| v0.6.0 | Performance baseline results |
| v0.7.0 | Lightweight load testing |
| v0.8.0 | Section 508-oriented accessibility smoke validation |
| v0.9.0 | Release quality gate results |
| v1.0.0 | Reliability SDET project baseline |
| v1.1.0 | Continuous Integration quality gate expansion |
| v1.2.0 | API contract validation |
| v1.3.0 | Accessibility scan validation |
| v1.4.0 | PostgreSQL schema and synthetic seed data validation |
| v1.5.0 | PostgreSQL-backed patient lookup validation |
| v1.6.0 | API-to-database consistency validation |
| v1.7.0 | PostgreSQL query plan and index validation |
| v1.8.0 | Controlled defect detection validation |
| v1.9.0 | Dependency cleanup and dependency security quality gate |

## v1.9.0 Dependency Security Work

The v1.9.0 milestone added dependency cleanup and dependency security quality gate behavior.

Work completed:

- cleaned the Python dependency list
- removed unused Python packages
- removed an unused dashboard script that required `pandas` and `matplotlib`
- updated `pytest` to resolve a Python audit finding
- added `scripts/validate_dependency_security.ps1`
- documented Newman/Postman transitive Node audit findings
- classified the full Node development/test-tooling audit as advisory
- integrated dependency security validation into the release quality gate

The release decision avoids blindly running:

    npm audit fix --force

The current audit output indicates that the forced fix would downgrade Newman in a breaking way.

The project documents that risk instead of applying an unsafe automatic fix.

## Documentation and Reports

Key documentation:

| Document | Purpose |
|---|---|
| `docs/RELEASE_QUALITY_GATES.md` | Release quality gate behavior |
| `docs/DEPENDENCY_SECURITY_QUALITY_GATE.md` | Dependency cleanup and dependency security validation |
| `docs/POSTGRESQL_SCHEMA.md` | PostgreSQL schema and seed data |
| `docs/ACCESSIBILITY_SCAN_VALIDATION.md` | axe-core accessibility scan validation |
| `docs/SECTION_508_ACCESSIBILITY.md` | Section 508-oriented accessibility smoke validation |
| `docs/PERFORMANCE_BASELINE.md` | Performance baseline explanation |
| `docs/LIGHTWEIGHT_LOAD_TESTING.md` | Lightweight load testing explanation |
| `docs/METRICS_AND_PERFORMANCE_BASELINE.md` | Metrics and baseline foundation |
| `docs/REQUEST_ID_TRACEABILITY.md` | Request identifier traceability |
| `docs/DIAGNOSTIC_LOGGING.md` | Diagnostic logging and request timing |

Key reports:

| Report | Purpose |
|---|---|
| `reports/release_quality_gate_v1.9.0.md` | Integrated v1.9.0 release quality gate result |
| `reports/dependency_security_quality_gate_v1.9.0.md` | Dependency cleanup and security gate report |
| `reports/performance_baseline_quality_gate_v1.9.0.md` | v1.9.0 performance baseline output |
| `reports/lightweight_load_test_quality_gate_v1.9.0.md` | v1.9.0 lightweight load test output |
| `reports/controlled_defect_detection_v1.8.0.md` | Controlled defect detection result |
| `reports/postgresql_query_plan_index_validation_v1.7.0.md` | Query plan/index validation result |
| `reports/api_database_consistency_validation_v1.6.0.md` | API/database consistency result |
| `reports/postgresql_backed_patient_lookup_v1.5.0.md` | PostgreSQL-backed API validation result |
| `reports/postgresql_schema_seed_data_v1.4.0.md` | Schema and seed data validation result |

## Reliability Value

The framework demonstrates that reliability validation is not a single test type.

It combines:

- functional validation
- contract validation
- regression testing
- observability
- accessibility awareness
- performance baselining
- lightweight load testing
- database consistency validation
- query plan review
- controlled defect detection
- dependency security review
- release gate reporting

The result is a repeatable validation process that makes release decisions more visible and less dependent on ad hoc judgment.

## Current Scope

This project is practice-scale.

It is designed to demonstrate quality engineering and reliability validation concepts in a controlled environment.

It is not a full enterprise production system, a real healthcare application, or a full security compliance program.

## Future Improvements

Possible future improvements include:

- add dependency security validation to GitHub Actions
- add Dependabot configuration
- generate a Software Bill of Materials
- add review dates for advisory dependency findings
- evaluate alternatives to Newman if transitive audit findings remain unresolved
- add stronger release threshold enforcement
- expand accessibility validation
- add additional database-volume query plan comparisons
