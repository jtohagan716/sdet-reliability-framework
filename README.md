# SDET Reliability Framework

A reliability-focused Software Development Engineer in Test (SDET) portfolio framework for validating Application Programming Interface (API) behavior, database state, observability evidence, retry safety, release-readiness checks, and healthcare interoperability scenarios.

This project demonstrates practical, transferable quality engineering skills across:

* API validation
* API contract validation
* PostgreSQL database validation
* automated pytest integration tests
* Docker Compose service orchestration
* OpenTelemetry trace correlation
* audit trail validation
* idempotency and retry safety
* dependency security review
* accessibility smoke validation
* performance and lightweight load testing
* synthetic Fast Healthcare Interoperability Resources (FHIR)-style validation
* stale-message protection for healthcare integration workflows

The focus is not just proving that happy-path requests work. The focus is proving that a system behaves safely under reliability risks such as retries, duplicate requests, broken healthcare references, out-of-order messages, stale updates, database inconsistency, and release quality gate failures.

## Project Purpose

This project is a practice-scale reliability validation framework.

It is not intended to be a complex business application, a production healthcare system, or a full FHIR server.

The purpose is to demonstrate how a system can be validated, observed, measured, tested under lightweight load, checked for accessibility smoke behavior, backed by deterministic PostgreSQL data, reviewed for dependency risk, and evaluated through repeatable release-readiness practices.

The healthcare interoperability module uses synthetic FHIR-style data to model realistic integration risks without using real patient data.

## Current Reliability Scenarios

This framework currently validates:

* PostgreSQL audit validation for encounter changes
* OpenTelemetry trace correlation from API requests to database behavior
* idempotency and retry-safety behavior for write-style API operations
* unsafe idempotency key reuse conflict detection
* Time To Live cleanup for idempotency records
* synthetic FHIR-style Patient, Encounter, Observation, and DiagnosticReport reference validation
* negative FHIR broken-reference detection
* PostgreSQL-backed FHIR validation evidence
* stale-message protection for out-of-order healthcare Encounter updates
* local Docker Compose validation with PostgreSQL, Prometheus, Grafana, Jaeger, and OpenTelemetry Collector

## Healthcare Interoperability Focus

The healthcare interoperability module uses synthetic FHIR-style resources and message events to model validation risks common in health IT integration work.

Current FHIR-related validation includes:

* valid Patient → Encounter → Observation → DiagnosticReport reference chains
* intentionally broken DiagnosticReport → Observation reference detection
* PostgreSQL evidence tables for validation run, resource check, and reference check results
* automated pytest validation of PostgreSQL evidence output
* stale-message protection where an older partial Encounter message cannot overwrite a newer complete Encounter state

No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## What This Project Demonstrates

This project demonstrates:

* Application Programming Interface (API) validation
* API contract validation
* automated regression testing
* Postman/Newman API regression checks
* Playwright browser and workflow automation
* Docker-based local runtime validation
* diagnostic logging
* request identifier traceability
* Prometheus metrics
* OpenTelemetry trace correlation
* Jaeger trace review
* performance baseline results
* lightweight load testing
* Section 508-oriented accessibility smoke validation
* axe-core accessibility scan validation
* PostgreSQL schema and seed data validation
* PostgreSQL-backed API behavior
* API-to-database consistency validation
* PostgreSQL query plan and index validation
* PostgreSQL audit validation
* database-backed validation evidence
* controlled defect detection validation
* dependency cleanup and dependency security review
* release quality gate results
* versioned release documentation
* synthetic FHIR-style resource validation
* healthcare reference integrity validation
* stale-message protection validation

## Local Reliability Stack

The local Docker Compose stack includes:

* FastAPI reliability API
* PostgreSQL
* Prometheus
* Grafana
* OpenTelemetry Collector
* Jaeger

The project combines automated tests, SQL validation scripts, documentation, and observable runtime behavior to produce repeatable evidence.

## Release Progression

* **v0.2.0** — REST Application Programming Interface (API) validation and smoke testing
* **v0.3.0** — Diagnostic logging and request timing
* **v0.4.0** — Request identifier traceability
* **v0.5.0** — Prometheus metrics and observability signals
* **v0.6.0** — Performance baseline results
* **v0.7.0** — Lightweight load testing
* **v0.8.0** — Section 508-oriented accessibility smoke validation
* **v0.9.0** — Release quality gate results
* **v1.0.0** — Reliability Software Development Engineer in Test (SDET) project baseline
* **v1.1.0** — Continuous Integration (CI) quality gate expansion
* **v1.2.0** — Application Programming Interface (API) contract validation
* **v1.3.0** — Accessibility scan validation
* **v1.4.0** — PostgreSQL schema and synthetic seed data validation
* **v1.5.0** — PostgreSQL-backed patient lookup validation
* **v1.6.0** — API-to-database consistency validation
* **v1.7.0** — PostgreSQL query plan and index validation
* **v1.8.0** — Controlled defect detection validation
* **v1.9.0** — Dependency cleanup and dependency security quality gate

## Technology Stack

* Python
* FastAPI
* Pytest
* PostgreSQL
* Psycopg
* Postman
* Newman
* Playwright
* axe-core for Playwright
* Docker
* Docker Compose
* Prometheus
* Grafana
* OpenTelemetry
* Jaeger
* Git
* GitHub
* GitHub Actions
* PowerShell
* Markdown documentation

## Main Endpoints

* **`/health`** — Basic service health check
* **`/patients/1001`** — Synthetic successful patient lookup
* **`/patients/1002`** — Synthetic secondary patient lookup
* **`/patients/1003`** — Additional synthetic patient lookup
* **`/patients/1004`** — Synthetic patient used for database consistency and defect-mode validation
* **`/patients/9999`** — Expected not-found lookup
* **`/patients/abc`** — Expected invalid-input response
* **`/metrics`** — Prometheus metrics endpoint
* **`/patient-lookup`** — Simple user-facing page for accessibility smoke validation
* **`/qa/idempotency-validation`** — Local QA endpoint for idempotency and retry-safety validation
* **`/qa/audit-otel-validation`** — Local QA endpoint for audit and OpenTelemetry trace-correlation validation

## Validation Layers

### Pytest

Pytest validates backend behavior, Application Programming Interface (API) logic, contract expectations, page structure, workflow logic, security helper behavior, script helper functions, database validation behavior, and synthetic FHIR-style validation scenarios.

Run:

```powershell
python -m pytest
```

FHIR-focused tests include:

```powershell
python -m pytest tests/integration/test_fhir_resource_validation.py -v
python -m pytest tests/integration/test_fhir_postgres_validation_evidence.py -v
python -m pytest tests/integration/test_fhir_stale_message_protection.py -v
```

### Newman Application Programming Interface (API) Regression

Newman runs the Postman Application Programming Interface (API) regression collection from the command line.

Run:

```powershell
npm run postman:test
```

### Playwright Automation

Playwright validates browser-facing behavior, workflow behavior, and accessibility-oriented checks.

Run:

```powershell
npx playwright test
```

### Local Smoke Validation

The local smoke validation script checks Docker, Application Programming Interface (API) health, synthetic patient behavior, Pytest, and Newman together.

Run:

```powershell
.\scripts\local_smoke_validation.ps1
```

### Performance Baseline

The performance baseline script captures normal local response-time and error-rate results.

Run:

```powershell
python .\scripts\run_performance_baseline.py
```

### Lightweight Load Test

The lightweight load test script runs a weighted traffic mix with concurrency and captures throughput, response time, p95, p99, and scenario-level results.

Run:

```powershell
python .\scripts\run_lightweight_load_test.py
```

### PostgreSQL Schema Validation

The PostgreSQL schema validation script checks that the local database container is running, expected relational tables exist, deterministic seed data is loaded, and representative join behavior returns expected results.

Run:

```powershell
.\scripts\validate_postgresql_schema.ps1
```

### PostgreSQL-Backed Patient Lookup Validation

The PostgreSQL-backed patient lookup validation confirms that the API can return patient summary data from PostgreSQL while preserving the external API contract.

Run:

```powershell
.\scripts\validate_postgresql_patient_lookup.ps1
```

### API-to-Database Consistency Validation

The API-to-database consistency validation compares API responses against direct PostgreSQL query results.

Run:

```powershell
.\scripts\validate_api_database_consistency.ps1
```

### PostgreSQL Query Plan and Index Validation

The query plan validation checks that expected database indexes exist and that query plan evidence can be captured for patient lookup behavior.

Run:

```powershell
.\scripts\validate_patient_lookup_query_plan.ps1
```

### PostgreSQL Audit Validation

The PostgreSQL audit validation checks encounter audit behavior for insert and update actions.

It verifies that audit rows capture change metadata and supports trace-correlation evidence through OpenTelemetry-related fields.

Run the SQL validation script through Docker Compose:

```powershell
Get-Content scripts\validate_encounter_audit.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Run the automated integration test:

```powershell
python -m pytest tests/integration/test_encounter_audit_validation.py -v
```

### Idempotency and Retry-Safety Validation

The idempotency validation proves that write-style API retry behavior is safe.

Core behavior:

```text
Same idempotency key + same request:
  replay the original stored response

Same idempotency key + different request:
  reject as a conflict
```

Run:

```powershell
python -m pytest tests/integration/test_idempotency_validation.py -v
```

### FHIR Reference Validation

The FHIR reference validation checks synthetic Patient, Encounter, Observation, and DiagnosticReport fixtures.

It validates:

* expected `resourceType` values
* valid cross-resource references
* absence of unresolved references in the valid fixture set
* detection of an intentionally broken DiagnosticReport → Observation reference

Run:

```powershell
python -m pytest tests/integration/test_fhir_resource_validation.py -v
```

### FHIR PostgreSQL Validation Evidence

The PostgreSQL FHIR validation evidence script proves that FHIR-style validation findings can be represented as queryable database evidence.

Run:

```powershell
Get-Content scripts\validate_fhir_reference_validation_evidence.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Run the automated integration test:

```powershell
python -m pytest tests/integration/test_fhir_postgres_validation_evidence.py -v
```

### FHIR Stale Message Protection

The stale-message protection validation models an out-of-order healthcare Encounter update scenario.

Scenario:

```text
Message 2 arrives first:
  sequence_number = 2
  status = finished
  completeness = complete

Message 1 arrives second:
  sequence_number = 1
  status = in-progress
  completeness = partial

Expected:
  sequence 2 remains current
  older partial message is marked stale
  newer complete state is not overwritten
```

Run:

```powershell
python -m pytest tests/integration/test_fhir_stale_message_protection.py -v
```

### Controlled Defect Detection Validation

The controlled defect detection validation intentionally enables a known defect mode, verifies that the API-to-database consistency check detects the defect, and restores normal behavior.

Run:

```powershell
.\scripts\validate_controlled_defect_detection.ps1
```

This validation is intentionally separate from the default release gate because it toggles defect behavior and recreates the API container.

### Dependency Security Quality Gate

The dependency security quality gate validates Python dependency health, Python vulnerability status, and Node dependency audit posture.

Run:

```powershell
.\scripts\validate_dependency_security.ps1
```

The script treats Python dependency health, Python vulnerability audit, and Node production/runtime audit as blocking checks.

The full Node development/test-tooling audit is advisory because current Newman/Postman transitive findings require impact analysis rather than a breaking forced downgrade.

### Release Quality Gate

The release quality gate script runs the major validation checks and generates release-readiness results.

Run:

```powershell
.\scripts\run_release_quality_gate.ps1
```

Optional controlled defect validation can be included with:

```powershell
.\scripts\run_release_quality_gate.ps1 -IncludeControlledDefectValidation
```

## Reports

Key generated reports include:

### Performance and Load Testing

* `reports/performance_baseline_v0.6.0.md`
  Initial performance baseline results.

* `reports/lightweight_load_test_v0.7.0.md`
  Initial lightweight load test results.

* `reports/performance_baseline_quality_gate_v0.9.0.md`
  Initial quality-gate-specific performance baseline results.

* `reports/lightweight_load_test_quality_gate_v0.9.0.md`
  Initial quality-gate-specific lightweight load test results.

* `reports/performance_baseline_quality_gate_v1.9.0.md`
  v1.9.0 quality-gate-specific performance baseline results.

* `reports/lightweight_load_test_quality_gate_v1.9.0.md`
  v1.9.0 quality-gate-specific lightweight load test results.

### Accessibility

* `reports/accessibility_smoke_v0.8.0.md`
  Section 508-oriented accessibility smoke report.

### Release Quality Gates

* `reports/release_quality_gate_v0.9.0.md`
  Initial release quality gate results.

* `reports/release_quality_gate_v1.9.0.md`
  Integrated v1.9.0 release quality gate results.

### PostgreSQL Validation

* `reports/postgresql_schema_seed_data_v1.4.0.md`
  PostgreSQL schema and seed data validation results.

* `reports/postgresql_backed_patient_lookup_v1.5.0.md`
  PostgreSQL-backed patient lookup validation results.

* `reports/api_database_consistency_validation_v1.6.0.md`
  API-to-database consistency validation results.

* `reports/postgresql_query_plan_index_validation_v1.7.0.md`
  PostgreSQL query plan and index validation results.

* `reports/postgresql_query_plan_index_comparison_v1.7.0.md`
  PostgreSQL query plan index comparison results.

### Defect Detection and Dependency Review

* `reports/controlled_defect_detection_v1.8.0.md`
  Controlled defect detection validation results.

* `reports/dependency_security_quality_gate_v1.9.0.md`
  Dependency cleanup and dependency security quality gate report.

## Documentation

Key documentation includes:

### Project and Release Process

* [Project Walkthrough](docs/PROJECT_WALKTHROUGH.md)
  Reviewer-friendly explanation of the project.

* [Release Quality Gates](docs/RELEASE_QUALITY_GATES.md)
  Release quality gate documentation.

* [Dependency Security Quality Gate](docs/DEPENDENCY_SECURITY_QUALITY_GATE.md)
  Dependency cleanup and dependency security quality gate documentation.

### Accessibility and Performance

* [Section 508 Accessibility](docs/SECTION_508_ACCESSIBILITY.md)
  Section 508-oriented accessibility smoke validation.

* [Accessibility Scan Validation](docs/ACCESSIBILITY_SCAN_VALIDATION.md)
  Accessibility scan validation documentation.

* [Lightweight Load Testing](docs/LIGHTWEIGHT_LOAD_TESTING.md)
  Lightweight load testing documentation.

* [Performance Baseline](docs/PERFORMANCE_BASELINE.md)
  Performance baseline documentation.

* [Metrics and Performance Baseline](docs/METRICS_AND_PERFORMANCE_BASELINE.md)
  Metrics and baseline foundation.

* [Portfolio Review Guide](docs/PORTFOLIO_REVIEW_GUIDE.md)  
  Reviewer-focused guide showing how the project demonstrates API behavior, database validation, audit evidence, observability, retry safety, and healthcare-style data quality validation.

### Observability and Runtime Diagnostics

* [Request ID Traceability](docs/REQUEST_ID_TRACEABILITY.md)
  Request identifier traceability.

* [Diagnostic Logging](docs/DIAGNOSTIC_LOGGING.md)
  Diagnostic logging and request timing.

* [Observability and OpenTelemetry](docs/OBSERVABILITY.md)
  OpenTelemetry, Jaeger, and trace-correlation documentation.

* [Ports and Protocols](docs/PORTS-AND-PROTOCOLS.md)
  Local service ports and protocol reference.

### PostgreSQL and Reliability Validation

* [PostgreSQL Schema](docs/POSTGRESQL_SCHEMA.md)
  PostgreSQL schema and seed data documentation.

* [PostgreSQL Audit Validation](docs/AUDIT-VALIDATION.md)
  Encounter audit validation and database evidence.

* [Idempotency and Retry Safety](docs/IDEMPOTENCY-AND-RETRY-SAFETY.md)
  Idempotency key validation, replay behavior, conflict detection, and cleanup.

### Healthcare Interoperability

* [FHIR Interoperability Roadmap](docs/FHIR-INTEROPERABILITY-ROADMAP.md)
  Healthcare interoperability roadmap for synthetic FHIR-style validation.

* [FHIR Reference Validation](docs/FHIR-REFERENCE-VALIDATION.md)
  Positive and negative synthetic FHIR reference validation.

* [FHIR PostgreSQL Validation Evidence](docs/FHIR-POSTGRES-VALIDATION-EVIDENCE.md)
  PostgreSQL-backed evidence for FHIR validation findings.

* [FHIR Stale Message Protection](docs/FHIR-STALE-MESSAGE-PROTECTION.md)
  Out-of-order healthcare message handling and stale-update protection.

  - [FHIR Stale Message PostgreSQL Evidence](docs/FHIR-STALE-MESSAGE-POSTGRES-EVIDENCE.md)  
  PostgreSQL-backed evidence for append-only message history, protected current Encounter state, and archived stale-message decisions.

  - [Patient Data Quality Review Queue](docs/PATIENT-DATA-QUALITY-REVIEW-QUEUE.md)  
  Documents how stale-message decisions can create reviewable patient data quality items with preserved review action history.

  - [Data Quality Work Queue Retry and Dead-Letter Validation](docs/DATA-QUALITY-WORK-QUEUE-RETRY-DEAD-LETTER.md)  
  Documents retry scheduling, max-attempt enforcement, dead-letter handling, error preservation, and queue failure history validation.

- [Query Performance Baseline Validation](docs/QUERY-PERFORMANCE-BASELINE.md)  
  Documents the first PostgreSQL query performance baseline, including EXPLAIN ANALYZE evidence, timing capture, queue linkage validation, and the decision to measure before tuning.  

- [Query Performance Tuning Comparison](docs/QUERY-PERFORMANCE-TUNING-COMPARISON.md)  
  Documents pre/post PostgreSQL query tuning evidence, targeted composite index validation, execution-plan comparison, and honest interpretation of local synthetic performance results.

- [API Endpoint Performance Baseline](docs/API-ENDPOINT-PERFORMANCE-BASELINE.md)  
  Documents API-layer response-time baseline validation for `/health` and `/qa/data-quality-review-items`, including request count, status codes, mean/median/p95 latency, payload size, and cleanup evidence.

- [Queue Performance Metrics Baseline](docs/QUEUE-PERFORMANCE-METRICS-BASELINE.md)  
  Documents queue health baseline validation, including queue depth, status distribution, retry pressure, dead-letter visibility, backlog age, processing lock age, and history action metrics.

## Synthetic FHIR Test Data

FHIR-style synthetic fixtures are stored under:

```text
test_data/fhir/
```

Current fixture areas include:

```text
test_data/fhir/patient-example.json
test_data/fhir/encounter-example.json
test_data/fhir/observation-example.json
test_data/fhir/diagnosticreport-example.json
test_data/fhir/invalid/
test_data/fhir/message_events/
```

The initial resource chain is:

```text
Patient/example-patient-001
  -> Encounter/example-encounter-001
    -> Observation/example-observation-001
      -> DiagnosticReport/example-diagnosticreport-001
```

The stale-message scenario uses synthetic Encounter message events to prove that an older partial message cannot overwrite a newer complete Encounter state.

## Dependency Security Notes

The project dependency set was cleaned during v1.9.0.

The Python dependency file was reduced to intentional project dependencies, and an initial Python audit finding was remediated by updating `pytest`.

The current dependency security process separates blocking checks from advisory findings.

Current policy:

* Python dependency health is blocking.
* Python vulnerability audit is blocking.
* Node production/runtime audit is blocking.
* Full Node development/test-tooling audit is advisory.
* Newman/Postman transitive audit findings are documented and monitored.
* Breaking forced dependency fixes are not applied without impact analysis.

## Testing and Certification Alignment

This project reinforces concepts from the International Software Testing Qualifications Board (ISTQB) Certified Tester Foundation Level (CTFL), including:

* regression testing
* confirmation testing
* test results
* acceptance criteria
* exit criteria
* test completion criteria
* risk-based testing
* release readiness

It also reinforces Department of Homeland Security (DHS) / Section 508 accessibility awareness, including:

* accessible labels
* keyboard reachability
* visible feedback
* page structure
* accessibility as part of release readiness

This project does not claim full Section 508 certification. It includes Section 508-oriented accessibility smoke validation and automated accessibility scan validation that can be expanded later.

## Data Safety

All project data is synthetic.

No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## Current Scope

This is a practice-scale project.

It is designed to demonstrate modern quality engineering and reliability validation practices in a controlled, explainable environment.

It is not intended to represent a full enterprise production system, full production healthcare system, or full FHIR implementation.

## Future Improvements

Planned or possible future improvements include:

* add PostgreSQL evidence for stale-message decisions
* add validation run cleanup strategy
* generate validation evidence from Python instead of static SQL
* add local HAPI FHIR server validation
* add Synthea-generated synthetic FHIR data
* add OpenTelemetry trace correlation for FHIR validation workflows
* add dependency security validation to GitHub Actions
* add Dependabot configuration
* generate a Software Bill of Materials
* add accepted-risk review dates for advisory dependency findings
* evaluate alternatives to Newman if transitive audit findings remain unresolved
* performance threshold enforcement
* baseline comparison reports
* expanded accessibility testing
* Department of Homeland Security (DHS) Trusted Tester study alignment
