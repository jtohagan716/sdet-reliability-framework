# SDET Reliability Framework

A reliability-focused Software Development Engineer in Test (SDET) portfolio project for validating Application Programming Interface (API) behavior, PostgreSQL data, observability evidence, retry safety, healthcare data workflows, performance, accessibility, and release readiness.

The framework demonstrates API and contract testing, Pytest integration testing, PostgreSQL validation, Docker Compose orchestration, OpenTelemetry tracing, audit validation, idempotency, retry and dead-letter behavior, accessibility scanning, performance testing, synthetic healthcare data validation, dependency review, and repeatable release quality gates.

Its purpose is not merely to prove that successful requests work. It evaluates whether a system behaves safely when exposed to duplicate requests, retries, broken data relationships, stale or out-of-order messages, database inconsistencies, processing failures, and release-quality risks.

## Project Scope

This is a practice-scale quality engineering and reliability framework. It is not a production healthcare system, complete interoperability platform, formal compliance assessment, or substitute for production security and performance testing.

The project demonstrates how an application can be:

* tested through API, browser, database, and workflow layers
* backed by deterministic PostgreSQL data
* observed through logs, metrics, and distributed traces
* measured through repeatable performance tests
* protected from duplicate, stale, and conflicting updates
* evaluated through repeatable release-readiness checks

All healthcare-related records and message events are synthetic.

## Reliability Coverage

| Area              | Validation performed                                                                                                                |
| ----------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| API quality       | Successful responses, invalid input, not-found behavior, contract preservation, payload validation, and API-to-database consistency |
| PostgreSQL        | Schema, seed data, joins, audit triggers, query plans, indexes, rollback behavior, and stored validation evidence                   |
| Retry safety      | Idempotent replay, conflicting key reuse, record expiration, retry scheduling, and maximum-attempt enforcement                      |
| Healthcare data   | Record relationships, broken references, stale updates, out-of-order messages, and preservation of newer state                      |
| Queue reliability | Review items, retry history, dead-letter transitions, error preservation, backlog age, and processing locks                         |
| Observability     | Diagnostic logs, request identifiers, Prometheus metrics, OpenTelemetry traces, Jaeger review, and API-to-database correlation      |
| Performance       | Response-time baselines, concurrency, throughput, error rate, p95 and p99 latency, and query tuning comparisons                     |
| Accessibility     | Labels, keyboard access, visible feedback, page structure, smoke checks, and axe-core scanning                                      |
| Release readiness | Integrated automated checks, dependency review, performance thresholds, reports, and pass/fail evidence                             |

## Technology Stack

Python · FastAPI · Pytest · PostgreSQL · Psycopg · Postman · Newman · Playwright · axe-core · Docker · Docker Compose · Prometheus · Grafana · OpenTelemetry · Jaeger · Git · GitHub · GitHub Actions · PowerShell

## Repository Structure

```text
api_service/    FastAPI application and database access
db/             PostgreSQL schema and stored database logic
docs/           Project and validation documentation
framework/      Reusable testing and reporting components
monitoring/     Prometheus and Grafana configuration
otel/           OpenTelemetry Collector configuration
reports/        Generated validation and release evidence
scripts/        PowerShell, Python, and SQL validation scripts
test_data/      Synthetic test fixtures
tests/          Automated regression and integration tests
```

## Local Reliability Stack

The Docker Compose environment includes FastAPI, PostgreSQL, Prometheus, Grafana, OpenTelemetry Collector, and Jaeger.

Start the environment:

```powershell
docker compose up -d --build
docker compose ps
```

Primary local ports:

| Service    |  Port |
| ---------- | ----: |
| FastAPI    |  8000 |
| Grafana    |  3000 |
| Prometheus |  9090 |
| Jaeger     | 16686 |
| PostgreSQL |  5432 |

See the ports and protocols documentation for the complete service reference.

## Main Endpoints

| Endpoint                        | Purpose                                      |
| ------------------------------- | -------------------------------------------- |
| `/health`                       | Service-health validation                    |
| `/patients/1001`                | Successful synthetic patient lookup          |
| `/patients/1002`                | Secondary synthetic patient lookup           |
| `/patients/1003`                | Additional synthetic patient lookup          |
| `/patients/1004`                | Consistency and controlled-defect validation |
| `/patients/9999`                | Expected not-found response                  |
| `/patients/abc`                 | Expected invalid-input response              |
| `/metrics`                      | Prometheus metrics                           |
| `/patient-lookup`               | Browser-facing accessibility smoke page      |
| `/qa/idempotency-validation`    | Idempotency and retry-safety validation      |
| `/qa/audit-otel-validation`     | Audit and trace-correlation validation       |
| `/qa/data-quality-review-items` | Reviewable healthcare data-quality items     |

## Running the Validation Layers

### Pytest

Pytest validates API behavior, contracts, PostgreSQL logic, audit evidence, retry safety, healthcare data relationships, queue processing, helper functions, controlled failures, and cleanup behavior.

```powershell
python -m pytest
python -m pytest tests/integration -v
```

### Newman API Regression

```powershell
npm run postman:test
```

### Playwright Automation

```powershell
npx playwright test
```

### Local Smoke Validation

The smoke script checks Docker availability, API health, patient behavior, Pytest, and Newman.

```powershell
.\scripts\local_smoke_validation.ps1
```

## PostgreSQL Validation

### Schema and Seed Data

Confirms that expected tables exist, deterministic synthetic records are loaded, and representative relational joins return the expected results.

```powershell
.\scripts\validate_postgresql_schema.ps1
```

### PostgreSQL-Backed API Behavior

Confirms that patient information is retrieved from PostgreSQL while preserving the external API contract.

```powershell
.\scripts\validate_postgresql_patient_lookup.ps1
```

### API-to-Database Consistency

Compares API responses with direct PostgreSQL query results to detect incorrect rows, unexpected transformations, and controlled defects.

```powershell
.\scripts\validate_api_database_consistency.ps1
```

### Query Plan and Index Validation

Captures PostgreSQL execution plans and verifies expected indexes.

```powershell
.\scripts\validate_patient_lookup_query_plan.ps1
```

The project measures query behavior before tuning, applies targeted changes, and records an honest pre-tuning and post-tuning comparison.

### Audit Validation

The encounter audit validation checks insert and update behavior and verifies operation type, old and new values, change source, changed-by metadata, timestamps, and trace-correlation fields.

```powershell
Get-Content scripts\validate_encounter_audit.sql |
    docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability

python -m pytest tests/integration/test_encounter_audit_validation.py -v
```

Audit tests run inside a transaction and roll back their changes so repeated executions do not leave test records behind.

## Idempotency and Retry Safety

The idempotency scenario validates safe handling of repeated write requests:

```text
Same idempotency key and same request:
Return the original stored response.

Same idempotency key and different request:
Reject the request as a conflict.
```

Validation also covers request fingerprints, response replay, conflict detection, expiration, Time To Live cleanup, and deterministic test cleanup.

```powershell
python -m pytest tests/integration/test_idempotency_validation.py -v
```

## Healthcare Data Reliability

Synthetic patient, encounter, observation, and diagnostic records model common data-quality and integration risks.

Validation includes:

* expected record types
* valid cross-record relationships
* missing and intentionally broken references
* PostgreSQL-backed validation findings
* append-only message history
* stale and out-of-order message detection
* preservation of newer and more complete record state
* data-quality review items
* retry and dead-letter handling

No real patient data, protected health information, personally identifiable information, production credentials, secrets, or production records are used.

### Stale-Message Scenario

```text
Newer message arrives first:
sequence number = 2
status = finished
completeness = complete

Older message arrives second:
sequence number = 1
status = in-progress
completeness = partial
```

Expected behavior:

* sequence 2 remains current
* the older message is marked stale
* the partial state does not overwrite the newer complete state
* message history and the stale decision are preserved
* a review item can be created when human attention is appropriate

This demonstrates that successful message processing is insufficient unless the resulting state also remains correct.

## Data-Quality Review Queue

Validation covers creation and management of reviewable healthcare data-quality items, including source linkage, status, priority, reviewer notes, action history, and preservation of the original reason for review.

The workflow provides a traceable path from automated detection to human review.

## Retry and Dead-Letter Processing

Queue reliability scenarios validate:

* retry scheduling
* attempt tracking
* maximum-attempt enforcement
* next-attempt timestamps
* processing locks
* preserved error details
* dead-letter transitions
* queue and action history

The goal is to prove that failed work is neither retried indefinitely nor discarded without useful evidence.

## Queue Health Metrics

Operational measurements include:

* total queue depth
* status distribution
* pending and retrying work
* dead-letter count
* oldest backlog age
* stale processing-lock age
* action-history totals

These measurements help distinguish a queue that is technically running from one that is healthy and supportable.

## Observability

The framework combines:

* structured diagnostic logging
* request identifiers
* Prometheus metrics
* OpenTelemetry tracing
* Jaeger trace review
* API-to-database trace correlation
* service-readiness checks
* queue-health reporting
* consolidated reliability summaries

Observability evidence is used to explain what happened during a test, not merely whether the test passed.

## Performance Validation

### Performance Baseline

```powershell
python .\scripts\run_performance_baseline.py
```

Captures request count, successful and failed requests, mean and median response time, p95 and p99 latency, and error rate.

### Lightweight Load Test

```powershell
python .\scripts\run_lightweight_load_test.py
```

Runs a weighted traffic mix with concurrency and records throughput, latency distribution, error rate, and scenario-level results.

These tests provide repeatable local evidence. They are not presented as enterprise-scale production capacity results.

## Controlled Defect Detection

A known inconsistency can be enabled deliberately so the API-to-database validation proves that it detects a meaningful failure.

```powershell
.\scripts\validate_controlled_defect_detection.ps1
```

The process then restores normal behavior. It remains separate from the default release gate because it intentionally modifies the runtime configuration.

## Dependency Security

```powershell
.\scripts\validate_dependency_security.ps1
```

Current policy:

* Python dependency health is blocking.
* Python vulnerability findings are blocking.
* Node production and runtime findings are blocking.
* Development and test-tooling findings may remain advisory when remediation requires impact analysis.
* Breaking forced upgrades are not applied without review.

This keeps known findings visible without introducing unreviewed dependency changes that could destabilize the project.

## Release Quality Gate

```powershell
.\scripts\run_release_quality_gate.ps1
```

Optional controlled-defect execution:

```powershell
.\scripts\run_release_quality_gate.ps1 -IncludeControlledDefectValidation
```

The gate combines API, database, Pytest, Newman, Playwright, accessibility, performance, dependency, and reporting checks into one repeatable release-readiness decision.

## Reports and Documentation

Generated evidence is stored under `reports/`. Project explanations and validation procedures are stored under `docs/`.

Coverage includes:

| Category          | Examples                                                                                   |
| ----------------- | ------------------------------------------------------------------------------------------ |
| Performance       | Baselines, load tests, endpoint timing, query comparisons                                  |
| Accessibility     | Smoke validation and automated scan results                                                |
| PostgreSQL        | Schema, seed data, consistency, query plans, indexes, and audits                           |
| Reliability       | Idempotency, stale messages, queue behavior, controlled defects, and observability         |
| Release readiness | Integrated quality gates, dependency results, and versioned evidence                       |
| Healthcare data   | Reference integrity, stored findings, review queues, message history, and failure recovery |

Generated reports describe results from the documented local environment and test conditions. They are not universal production-performance or compliance claims.

## Selected Release Milestones

| Version | Milestone                                     |
| ------- | --------------------------------------------- |
| v0.2.0  | API validation and smoke testing              |
| v0.3.0  | Diagnostic logging and request timing         |
| v0.4.0  | Request identifier traceability               |
| v0.5.0  | Prometheus metrics                            |
| v0.6.0  | Performance baselines                         |
| v0.7.0  | Lightweight load testing                      |
| v0.8.0  | Accessibility smoke validation                |
| v0.9.0  | Release quality gate                          |
| v1.0.0  | Reliability SDET baseline                     |
| v1.1.0  | Continuous Integration quality-gate expansion |
| v1.2.0  | API contract validation                       |
| v1.3.0  | Automated accessibility scanning              |
| v1.4.0  | PostgreSQL schema and seed-data validation    |
| v1.5.0  | PostgreSQL-backed patient lookup              |
| v1.6.0  | API-to-database consistency                   |
| v1.7.0  | Query-plan and index validation               |
| v1.8.0  | Controlled defect detection                   |
| v1.9.0  | Dependency security quality gate              |

Later development adds audit validation, trace correlation, retry safety, healthcare data-quality workflows, review queues, dead-letter handling, queue metrics, observability readiness, and consolidated reliability reporting.

## Testing and Accessibility Reference Points

The project reinforces testing concepts commonly covered by the International Software Testing Qualifications Board (ISTQB) Certified Tester Foundation Level (CTFL), including regression testing, confirmation testing, risk-based testing, acceptance and exit criteria, test evidence, defect detection, and release readiness.

It also applies practical accessibility considerations associated with Section 508-oriented testing, including labels, keyboard access, visible feedback, page structure, automated scanning, and accessibility checks within release workflows.

These references provide educational and technical context. They do not represent formal certification, a compliance determination, government approval, agency endorsement, or alignment with the requirements of a particular organization.

## Data Safety and Limitations

All project data is synthetic. The repository does not use real patient data, protected health information, personally identifiable information, production credentials, secrets, or production database records.

The framework is designed to be locally executable, repeatable, inspectable, and explainable. It does not reproduce the scale, security model, availability requirements, or regulatory responsibilities of a production enterprise system.

## Future Improvements

* expand automated PostgreSQL evidence generation
* add larger generated synthetic healthcare datasets
* extend healthcare data-quality and recovery scenarios
* correlate additional workflows through OpenTelemetry
* add dependency checks and Dependabot to GitHub Actions
* generate a Software Bill of Materials
* track accepted dependency risks and review dates
* expand historical performance comparison and threshold enforcement
* add queue saturation and recovery testing
* broaden accessibility coverage using publicly available guidance
* add additional controlled failure scenarios
* strengthen Continuous Integration environment-drift detection

## Project Principle

Reliable testing should produce more than a passing result. It should create repeatable evidence showing what was tested, what was expected, what occurred, what data changed, what evidence was captured, what failed, why it failed, whether cleanup succeeded, and whether the system is ready to proceed.
