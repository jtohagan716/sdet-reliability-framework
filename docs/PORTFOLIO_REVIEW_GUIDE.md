# Portfolio Review Guide

## Purpose

This guide helps reviewers quickly understand what the SDET Reliability Framework demonstrates.

The project is designed to show reliability-focused quality engineering across several layers:

* Application Programming Interface (API) behavior
* PostgreSQL database state
* audit and validation evidence
* observability and traceability
* retry safety
* healthcare-style data quality risks
* repeatable release-readiness validation

The goal is not to present a production healthcare system.

The goal is to demonstrate practical Software Development Engineer in Test (SDET), Quality Assurance (QA), API testing, database validation, and reliability engineering skills in a controlled local framework.

## What This Project Proves

This project demonstrates that software quality validation can go beyond checking whether an endpoint returns a successful response.

The framework validates:

```text
API behavior
+ database state
+ audit evidence
+ traceability
+ negative-path behavior
+ healthcare-style data quality risk
```

A reviewer should be able to see that the project tests both functional behavior and the data layer behind that behavior.

## Fast Review Path

A reviewer can understand the core value of this project by reviewing these areas:

1. README project overview
2. API and database validation
3. PostgreSQL audit validation
4. OpenTelemetry trace correlation
5. idempotency and retry-safety validation
6. synthetic FHIR-style reference validation
7. stale-message protection
8. PostgreSQL-backed stale-message evidence
9. release notes and documentation

The strongest healthcare reliability proof point is the stale-message evidence scenario.

## Local Stack

The local Docker Compose stack includes:

* FastAPI reliability API
* PostgreSQL
* Prometheus
* Grafana
* OpenTelemetry Collector
* Jaeger

Start the stack with:

```powershell
docker compose up -d
```

Confirm services:

```powershell
docker compose ps
```

Check API health:

```powershell
Invoke-RestMethod http://localhost:8000/health
```

## Proof Point 1: API Behavior Is Validated

The project includes API validation for expected success, not-found, and invalid-input behavior.

Example endpoints:

```text
/health
/patients/1001
/patients/1002
/patients/1003
/patients/1004
/patients/9999
/patients/abc
/metrics
```

Run the main pytest suite with:

```powershell
python -m pytest
```

This demonstrates automated validation of API behavior and regression expectations.

## Proof Point 2: Database State Is Validated

The framework does not stop at API response validation.

It also validates PostgreSQL-backed data behavior.

Database validation areas include:

* PostgreSQL schema and seed data validation
* PostgreSQL-backed patient lookup validation
* API-to-database consistency validation
* PostgreSQL query plan and index validation
* PostgreSQL audit validation
* PostgreSQL-backed healthcare validation evidence

This demonstrates data-layer awareness.

A key idea in this project is:

```text
An API response is not enough evidence by itself.

The database state behind the response also matters.
```

## Proof Point 3: API-to-Database Consistency Is Checked

The project validates that API responses match direct PostgreSQL query results.

This is important because a system can appear correct at the API layer while still having incorrect or inconsistent database state.

Relevant validation area:

```text
API-to-database consistency validation
```

This supports a practical quality engineering question:

```text
Does the API result agree with the source data?
```

## Proof Point 4: Audit Evidence Is Validated

The project includes PostgreSQL audit validation for Encounter changes.

The audit validation checks that insert and update behavior creates reviewable database evidence.

Relevant files:

```text
db/sql/004_encounter_audit_logic.sql
scripts/validate_encounter_audit.sql
tests/integration/test_encounter_audit_validation.py
```

Run:

```powershell
python -m pytest tests/integration/test_encounter_audit_validation.py -v
```

This demonstrates that the framework validates more than final state.

It also validates evidence of how state changed.

## Proof Point 5: Observability Is Included

The project includes observability through:

* request identifier traceability
* diagnostic logging
* Prometheus metrics
* OpenTelemetry trace correlation
* Jaeger trace review

The goal is to make system behavior inspectable.

The project supports the idea that a reliability test should help answer:

```text
What happened?
Where did it happen?
Can the behavior be traced?
Can the evidence be reviewed?
```

Jaeger can be reviewed locally at:

```text
http://localhost:16686
```

## Proof Point 6: Idempotency and Retry Safety Are Validated

The framework validates retry-safe behavior for write-style API operations.

Core behavior:

```text
Same idempotency key + same request:
  replay the original stored response

Same idempotency key + different request:
  reject as a conflict
```

Relevant validation:

```text
tests/integration/test_idempotency_validation.py
```

This demonstrates awareness of real-world reliability risks such as:

* duplicate requests
* client retries
* timeout retries
* unsafe replay
* repeated submissions
* conflicting writes

## Proof Point 7: Synthetic FHIR-Style Reference Validation

The healthcare interoperability module uses synthetic FHIR-style resources.

Current synthetic resources include:

```text
Patient
Encounter
Observation
DiagnosticReport
```

Valid reference chain:

```text
Patient/example-patient-001
  -> Encounter/example-encounter-001
    -> Observation/example-observation-001
      -> DiagnosticReport/example-diagnosticreport-001
```

The framework validates that these references resolve correctly.

It also includes a negative scenario where a DiagnosticReport references a missing Observation.

Relevant test:

```text
tests/integration/test_fhir_resource_validation.py
```

Run:

```powershell
python -m pytest tests/integration/test_fhir_resource_validation.py -v
```

This demonstrates healthcare data relationship validation without claiming to be a full FHIR implementation.

## Proof Point 8: PostgreSQL FHIR Validation Evidence

The project records synthetic FHIR-style validation results in PostgreSQL.

Relevant files:

```text
db/sql/009_fhir_reference_validation_evidence.sql
scripts/validate_fhir_reference_validation_evidence.sql
tests/integration/test_fhir_postgres_validation_evidence.py
```

Run:

```powershell
python -m pytest tests/integration/test_fhir_postgres_validation_evidence.py -v
```

This demonstrates that validation findings can be represented as queryable database evidence.

## Proof Point 9: Stale-Message Protection

The stale-message scenario models a healthcare integration risk where messages arrive out of order.

Scenario:

```text
Message 2 arrives first:
  resource: Encounter/example-encounter-001
  sequence_number: 2
  status: finished
  completeness: complete

Message 1 arrives second:
  resource: Encounter/example-encounter-001
  sequence_number: 1
  status: in-progress
  completeness: partial
```

Expected behavior:

```text
The newer complete Encounter message remains current.
The older partial Encounter message is preserved.
The older partial Encounter message is marked stale.
The current Encounter state is not downgraded.
```

Relevant test:

```text
tests/integration/test_fhir_stale_message_protection.py
```

Run:

```powershell
python -m pytest tests/integration/test_fhir_stale_message_protection.py -v
```

This demonstrates awareness of silent data quality failure risk.

## Proof Point 10: PostgreSQL Stale-Message Evidence

The strongest database-backed healthcare reliability scenario is the PostgreSQL stale-message evidence validation.

Relevant files:

```text
db/sql/010_fhir_stale_message_evidence.sql
scripts/validate_fhir_stale_message_evidence.sql
tests/integration/test_fhir_stale_message_postgres_evidence.py
docs/FHIR-STALE-MESSAGE-POSTGRES-EVIDENCE.md
```

The evidence model uses three tables:

```text
fhir_message_events
fhir_current_encounter_state
fhir_stale_message_decisions
```

The design separates:

```text
append-only message history
+ current-state projection
+ stale-message decision archive
```

Run the automated validation:

```powershell
python -m pytest tests/integration/test_fhir_stale_message_postgres_evidence.py -v
```

Run the SQL evidence script:

```powershell
Get-Content scripts\validate_fhir_stale_message_evidence.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

Expected evidence includes:

```text
protected_state_assertion | passed
stale_archive_assertion | passed
append_only_history_assertion | passed
ROLLBACK
```

The `ROLLBACK` is intentional.

It keeps the validation repeatable and deterministic.

## Why the Stale-Message Evidence Matters

The stale-message evidence scenario demonstrates that the framework can detect and preserve evidence around a data quality risk.

A weaker system might allow this:

```text
late older message arrives
current state is overwritten
finished becomes in-progress
no clear evidence explains why
```

This framework validates a safer pattern:

```text
late older message arrives
message history is preserved
current state is protected
stale decision is archived
reason is queryable
validation remains repeatable
```

This supports:

* data quality review
* production support analysis
* interface troubleshooting
* audit-style investigation
* reconciliation planning
* replay analysis
* prevention of silent state corruption

## Healthcare Scope Clarification

This project uses synthetic FHIR-style resources and message events.

It does not claim to be:

* a production healthcare system
* a full FHIR server
* a FHIR conformance suite
* an enterprise interface engine
* a clinical decision system
* an Electronic Health Record (EHR)

The healthcare scenarios are used to demonstrate reliability validation, data-layer validation, and healthcare-aware quality engineering.

## Data Safety

All data is synthetic.

The project does not use:

* real patient data
* protected health information
* personally identifiable information
* production credentials
* secrets
* production database exports

## Release Milestone

The current healthcare interoperability reliability baseline is:

```text
v2.0.0 — Healthcare Interoperability Reliability Baseline
```

This milestone includes:

* synthetic FHIR-style reference validation
* negative broken-reference detection
* PostgreSQL FHIR validation evidence
* stale-message protection
* PostgreSQL stale-message archive evidence
* automated pytest validation
* repeatable SQL validation with ROLLBACK
* clean documentation and release story

## Recommended Reviewer Commands

Start local services:

```powershell
docker compose up -d
```

Run the full test suite:

```powershell
python -m pytest
```

Run the healthcare interoperability validation group:

```powershell
python -m pytest tests/integration/test_fhir_resource_validation.py tests/integration/test_fhir_postgres_validation_evidence.py tests/integration/test_fhir_stale_message_protection.py tests/integration/test_fhir_stale_message_postgres_evidence.py -v
```

Run the PostgreSQL stale-message evidence script:

```powershell
Get-Content scripts\validate_fhir_stale_message_evidence.sql | docker compose exec -T postgres psql -x -U sdet_user -d sdet_reliability
```

## What This Demonstrates Professionally

This project demonstrates practical skills relevant to:

* Software Development Engineer in Test (SDET)
* Quality Assurance (QA) automation
* API testing
* database validation
* healthcare integration testing
* application support
* production support
* reliability engineering
* release-readiness validation

The project shows the ability to validate not only whether software responds, but whether it preserves correct state, rejects unsafe changes, records useful evidence, and remains repeatable.

## Summary

The SDET Reliability Framework demonstrates functional testing and data-layer validation together.

It validates API behavior, PostgreSQL state, audit evidence, traceability, retry safety, and healthcare-style data quality risks.

The strongest current proof point is the stale-message evidence scenario, which shows that the framework can preserve message history, protect current state, archive decision evidence, and prevent a silent downgrade of healthcare-style Encounter data.
