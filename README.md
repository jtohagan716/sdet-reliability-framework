# SDET Reliability Framework

A reliability-focused Software Development Engineer in Test (SDET) project demonstrating modern software quality, Application Programming Interface (API) validation, observability, performance results, accessibility smoke validation, PostgreSQL-backed validation, dependency security review, and repeatable release-readiness practices.

## Project Purpose

This project is a practice-scale reliability validation framework.

It is not intended to be a complex business application or a production healthcare system.

The purpose is to demonstrate how a system can be validated, observed, measured, tested under lightweight load, checked for accessibility smoke behavior, backed by deterministic PostgreSQL data, reviewed for dependency risk, and evaluated through a repeatable release quality gate.

## Reliability Scenarios Covered

This project validates several reliability-focused behaviors across API, database, observability, and test automation layers.

- PostgreSQL audit validation for encounter changes
- OpenTelemetry trace correlation from API requests to database behavior
- Idempotency and retry-safety validation
- Conflict detection for unsafe idempotency key reuse
- Time To Live cleanup for idempotency records
- Local Docker Compose validation with PostgreSQL, Prometheus, Grafana, Jaeger, and OpenTelemetry Collector

## What This Project Demonstrates

This project demonstrates:

- Application Programming Interface (API) validation
- API contract validation
- automated regression testing
- Postman/Newman API regression checks
- Playwright browser and workflow automation
- Docker-based local runtime validation
- diagnostic logging
- request identifier traceability
- Prometheus metrics
- performance baseline results
- lightweight load testing
- Section 508-oriented accessibility smoke validation
- axe-core accessibility scan validation
- PostgreSQL schema and seed data validation
- PostgreSQL-backed API behavior
- API-to-database consistency validation
- PostgreSQL query plan and index validation
- controlled defect detection validation
- dependency cleanup and dependency security review
- release quality gate results
- versioned release documentation

## Release Progression

| Release | Capability |
|---|---|
| v0.2.0 | REST Application Programming Interface (API) validation and smoke testing |
| v0.3.0 | Diagnostic logging and request timing |
| v0.4.0 | Request identifier traceability |
| v0.5.0 | Prometheus metrics and observability signals |
| v0.6.0 | Performance baseline results |
| v0.7.0 | Lightweight load testing |
| v0.8.0 | Section 508-oriented accessibility smoke validation |
| v0.9.0 | Release quality gate results |
| v1.0.0 | Reliability Software Development Engineer in Test (SDET) project baseline |
| v1.1.0 | Continuous Integration (CI) quality gate expansion |
| v1.2.0 | Application Programming Interface (API) contract validation |
| v1.3.0 | Accessibility scan validation |
| v1.4.0 | PostgreSQL schema and synthetic seed data validation |
| v1.5.0 | PostgreSQL-backed patient lookup validation |
| v1.6.0 | API-to-database consistency validation |
| v1.7.0 | PostgreSQL query plan and index validation |
| v1.8.0 | Controlled defect detection validation |
| v1.9.0 | Dependency cleanup and dependency security quality gate |

## Technology Stack

- Python
- FastAPI
- Pytest
- PostgreSQL
- Psycopg
- Postman
- Newman
- Playwright
- axe-core for Playwright
- Docker
- Docker Compose
- Prometheus
- Grafana
- Git
- GitHub
- GitHub Actions
- PowerShell
- Markdown documentation

## Main Endpoints

| Endpoint | Purpose |
|---|---|
| /health | Basic service health check |
| /patients/1001 | Synthetic successful patient lookup |
| /patients/1002 | Synthetic secondary patient lookup |
| /patients/1003 | Additional synthetic patient lookup |
| /patients/1004 | Synthetic patient used for database consistency and defect-mode validation |
| /patients/9999 | Expected not-found lookup |
| /patients/abc | Expected invalid-input response |
| /metrics | Prometheus metrics endpoint |
| /patient-lookup | Simple user-facing page for accessibility smoke validation |


## Validation Layers

### Pytest

Pytest validates backend behavior, Application Programming Interface (API) logic, contract expectations, page structure, workflow logic, security helper behavior, and script helper functions.

Run:

    python -m pytest

### Newman Application Programming Interface (API) Regression

Newman runs the Postman Application Programming Interface (API) regression collection from the command line.

Run:

    npm run postman:test

### Playwright Automation

Playwright validates browser-facing behavior, workflow behavior, and accessibility-oriented checks.

Run:

    npx playwright test

### Local Smoke Validation

The local smoke validation script checks Docker, Application Programming Interface (API) health, synthetic patient behavior, Pytest, and Newman together.

Run:

    .\scripts\local_smoke_validation.ps1

### Performance Baseline

The performance baseline script captures normal local response-time and error-rate results.

Run:

    python .\scripts\run_performance_baseline.py

### Lightweight Load Test

The lightweight load test script runs a weighted traffic mix with concurrency and captures throughput, response time, p95, p99, and scenario-level results.

Run:

    python .\scripts\run_lightweight_load_test.py

### PostgreSQL Schema Validation

The PostgreSQL schema validation script checks that the local database container is running, expected relational tables exist, deterministic seed data is loaded, and representative join behavior returns expected results.

Run:

    .\scripts\validate_postgresql_schema.ps1

### PostgreSQL-Backed Patient Lookup Validation

The PostgreSQL-backed patient lookup validation confirms that the API can return patient summary data from PostgreSQL while preserving the external API contract.

Run:

    .\scripts\validate_postgresql_patient_lookup.ps1

### API-to-Database Consistency Validation

The API-to-database consistency validation compares API responses against direct PostgreSQL query results.

Run:

    .\scripts\validate_api_database_consistency.ps1

### PostgreSQL Query Plan and Index Validation

The query plan validation checks that expected database indexes exist and that query plan evidence can be captured for patient lookup behavior.

Run:

    .\scripts\validate_patient_lookup_query_plan.ps1

### Controlled Defect Detection Validation

The controlled defect detection validation intentionally enables a known defect mode, verifies that the API-to-database consistency check detects the defect, and restores normal behavior.

Run:

    .\scripts\validate_controlled_defect_detection.ps1

This validation is intentionally separate from the default release gate because it toggles defect behavior and recreates the API container.

### Dependency Security Quality Gate

The dependency security quality gate validates Python dependency health, Python vulnerability status, and Node dependency audit posture.

Run:

    .\scripts\validate_dependency_security.ps1

The script treats Python dependency health, Python vulnerability audit, and Node production/runtime audit as blocking checks.

The full Node development/test-tooling audit is advisory because current Newman/Postman transitive findings require impact analysis rather than a breaking forced downgrade.

### Release Quality Gate

The release quality gate script runs the major validation checks and generates release-readiness results.

Run:

    .\scripts\run_release_quality_gate.ps1

Optional controlled defect validation can be included with:

    .\scripts\run_release_quality_gate.ps1 -IncludeControlledDefectValidation

## Reports

Key generated reports include:

| Report | Purpose |
|---|---|
| reports/performance_baseline_v0.6.0.md | Initial performance baseline results |
| reports/lightweight_load_test_v0.7.0.md | Initial lightweight load test results |
| reports/accessibility_smoke_v0.8.0.md | Section 508-oriented accessibility smoke report |
| reports/release_quality_gate_v0.9.0.md | Initial release quality gate results |
| reports/performance_baseline_quality_gate_v0.9.0.md | Initial quality-gate-specific performance baseline results |
| reports/lightweight_load_test_quality_gate_v0.9.0.md | Initial quality-gate-specific lightweight load test results |
| reports/postgresql_schema_seed_data_v1.4.0.md | PostgreSQL schema and seed data validation results |
| reports/postgresql_backed_patient_lookup_v1.5.0.md | PostgreSQL-backed patient lookup validation results |
| reports/api_database_consistency_validation_v1.6.0.md | API-to-database consistency validation results |
| reports/postgresql_query_plan_index_validation_v1.7.0.md | PostgreSQL query plan and index validation results |
| reports/postgresql_query_plan_index_comparison_v1.7.0.md | PostgreSQL query plan index comparison results |
| reports/controlled_defect_detection_v1.8.0.md | Controlled defect detection validation results |
| reports/dependency_security_quality_gate_v1.9.0.md | Dependency cleanup and dependency security quality gate report |
| reports/release_quality_gate_v1.9.0.md | Integrated v1.9.0 release quality gate results |
| reports/performance_baseline_quality_gate_v1.9.0.md | v1.9.0 quality-gate-specific performance baseline results |
| reports/lightweight_load_test_quality_gate_v1.9.0.md | v1.9.0 quality-gate-specific lightweight load test results |

## Documentation

Key documentation includes:

| Document | Purpose |
|---|---|
| docs/PROJECT_WALKTHROUGH.md | Reviewer-friendly explanation of the project |
| docs/RELEASE_QUALITY_GATES.md | Release quality gate documentation |
| docs/DEPENDENCY_SECURITY_QUALITY_GATE.md | Dependency cleanup and dependency security quality gate documentation |
| docs/SECTION_508_ACCESSIBILITY.md | Section 508-oriented accessibility smoke validation |
| docs/ACCESSIBILITY_SCAN_VALIDATION.md | Accessibility scan validation documentation |
| docs/POSTGRESQL_SCHEMA.md | PostgreSQL schema and seed data documentation |
| docs/LIGHTWEIGHT_LOAD_TESTING.md | Lightweight load testing documentation |
| docs/PERFORMANCE_BASELINE.md | Performance baseline documentation |
| docs/METRICS_AND_PERFORMANCE_BASELINE.md | Metrics and baseline foundation |
| docs/REQUEST_ID_TRACEABILITY.md | Request identifier traceability |
| docs/DIAGNOSTIC_LOGGING.md | Diagnostic logging and request timing |

## Documentation

- [PostgreSQL Audit Validation](docs/AUDIT-VALIDATION.md)
- [Observability and OpenTelemetry](docs/OBSERVABILITY.md)
- [Ports and Protocols](docs/PORTS-AND-PROTOCOLS.md)
- [Idempotency and Retry Safety](docs/IDEMPOTENCY-AND-RETRY-SAFETY.md)
- [FHIR Interoperability Roadmap](docs/FHIR-INTEROPERABILITY-ROADMAP.md)

## Healthcare Interoperability Validation

This project includes a healthcare interoperability validation module using synthetic FHIR-style resources.

The first phase validates a simple healthcare reference chain:

```text
Patient
  -> Encounter
    -> Observation
      -> DiagnosticReport

## Dependency Security Notes

The project dependency set was cleaned during v1.9.0.

The Python dependency file was reduced to intentional project dependencies, and an initial Python audit finding was remediated by updating `pytest`.

The current dependency security process separates blocking checks from advisory findings.

Current policy:

- Python dependency health is blocking.
- Python vulnerability audit is blocking.
- Node production/runtime audit is blocking.
- Full Node development/test-tooling audit is advisory.
- Newman/Postman transitive audit findings are documented and monitored.
- Breaking forced dependency fixes are not applied without impact analysis.

## Testing and Certification Alignment

This project reinforces concepts from the International Software Testing Qualifications Board (ISTQB) Certified Tester Foundation Level (CTFL), including:

- regression testing
- confirmation testing
- test results
- acceptance criteria
- exit criteria
- test completion criteria
- risk-based testing
- release readiness

It also reinforces Department of Homeland Security (DHS) / Section 508 accessibility awareness, including:

- accessible labels
- keyboard reachability
- visible feedback
- page structure
- accessibility as part of release readiness

This project does not claim full Section 508 certification. It includes Section 508-oriented accessibility smoke validation and automated accessibility scan validation that can be expanded later.

## Data Safety

All project data is synthetic.

No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## Current Scope

This is a practice-scale project.

It is designed to demonstrate modern quality engineering and reliability validation practices in a controlled, explainable environment.

It is not intended to represent a full enterprise production system.

## Future Improvements

Planned or possible future improvements include:

- add dependency security validation to GitHub Actions
- add Dependabot configuration
- generate a Software Bill of Materials
- add accepted-risk review dates for advisory dependency findings
- evaluate alternatives to Newman if transitive audit findings remain unresolved
- performance threshold enforcement
- baseline comparison reports
- expanded accessibility testing
- Department of Homeland Security (DHS) Trusted Tester study alignment
