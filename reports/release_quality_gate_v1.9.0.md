# Release Quality Gate Report

Generated UTC: `2026-07-07T04:26:59.1263508Z`
Total Gates: `16`
Passed: `15`
Failed: ``
Elapsed Seconds: `929.27`
Controlled Defect Validation Included: `False`

## Summary

| Gate | Status | Exit Code | Duration Seconds |
|---|---|---:|---:|
| Dependency security quality gate | PASS | 0 | 73.79 |
| Python syntax check - FastAPI app | PASS | 0 | 2.02 |
| Python syntax check - performance baseline script | PASS | 0 | 2.03 |
| Python syntax check - lightweight load test script | PASS | 0 | 1.04 |
| Full Pytest regression suite | PASS | 0 | 34.23 |
| Start Docker stack | PASS | 0 | 183.78 |
| PostgreSQL schema validation | PASS | 0 | 20.3 |
| PostgreSQL-backed patient lookup validation | PASS | 0 | 9.11 |
| API-to-database consistency validation | PASS | 0 | 3.05 |
| PostgreSQL query plan and index validation | PASS | 0 | 3.04 |
| Newman API regression | FAIL | 1 | 38.48 |
| Focused Section 508 accessibility smoke validation | PASS | 0 | 220.21 |
| Full Playwright automation | PASS | 0 | 122.82 |
| Performance baseline results | PASS | 0 | 22.3 |
| Lightweight load test results | PASS | 0 | 5.12 |
| Local Docker/API smoke validation | PASS | 0 | 186.87 |

## Gate Details

### Dependency security quality gate

Status: `PASS`

Command:

~~~powershell
.\scripts\validate_dependency_security.ps1
~~~

### Python syntax check - FastAPI app

Status: `PASS`

Command:

~~~powershell
python -m py_compile .\api_service\app.py
~~~

### Python syntax check - performance baseline script

Status: `PASS`

Command:

~~~powershell
python -m py_compile .\scripts\run_performance_baseline.py
~~~

### Python syntax check - lightweight load test script

Status: `PASS`

Command:

~~~powershell
python -m py_compile .\scripts\run_lightweight_load_test.py
~~~

### Full Pytest regression suite

Status: `PASS`

Command:

~~~powershell
python -m pytest
~~~

### Start Docker stack

Status: `PASS`

Command:

~~~powershell
docker compose up -d --build
~~~

### PostgreSQL schema validation

Status: `PASS`

Command:

~~~powershell
.\scripts\validate_postgresql_schema.ps1
~~~

### PostgreSQL-backed patient lookup validation

Status: `PASS`

Command:

~~~powershell
.\scripts\validate_postgresql_patient_lookup.ps1
~~~

### API-to-database consistency validation

Status: `PASS`

Command:

~~~powershell
.\scripts\validate_api_database_consistency.ps1
~~~

### PostgreSQL query plan and index validation

Status: `PASS`

Command:

~~~powershell
.\scripts\validate_patient_lookup_query_plan.ps1
~~~

### Newman API regression

Status: `FAIL`

Command:

~~~powershell
npm run postman:test
~~~

### Focused Section 508 accessibility smoke validation

Status: `PASS`

Command:

~~~powershell
npx playwright test tests/ui/patient_lookup_accessibility.spec.ts
~~~

### Full Playwright automation

Status: `PASS`

Command:

~~~powershell
npx playwright test
~~~

### Performance baseline results

Status: `PASS`

Command:

~~~powershell
python .\scripts\run_performance_baseline.py --output reports/performance_baseline_quality_gate_v1.9.0.md
~~~

### Lightweight load test results

Status: `PASS`

Command:

~~~powershell
python .\scripts\run_lightweight_load_test.py --output reports/lightweight_load_test_quality_gate_v1.9.0.md
~~~

### Local Docker/API smoke validation

Status: `PASS`

Command:

~~~powershell
.\scripts\local_smoke_validation.ps1
~~~

## Interpretation

This report captures release-readiness results for the project.

A passing quality gate means the selected automated checks completed successfully before release.

The gate includes dependency security validation, syntax checks, regression testing, Docker stack startup, Application Programming Interface (API) contract testing, Postman/Newman validation, Playwright automation, accessibility smoke validation, PostgreSQL schema validation, API-to-database consistency validation, query plan/index validation, performance baseline results, lightweight load testing, and Docker/API smoke validation.

## Dependency Security Connection

Dependency validation is included as part of release readiness. Python dependency health and Python vulnerability audit checks are blocking. Node production/runtime audit is blocking. The full Node development/test-tooling audit is handled inside the dependency security gate as an advisory review because current Newman/Postman findings require impact analysis rather than a forced breaking downgrade.

## Database Reliability Connection

PostgreSQL schema validation, PostgreSQL-backed patient lookup validation, API-to-database consistency validation, and query plan/index validation are included to confirm that backend data behavior remains stable after changes.

## International Software Testing Qualifications Board (ISTQB) / Certified Tester Foundation Level (CTFL) Connection

This workflow represents release exit criteria and regression results. The software should not be considered ready for release unless the required checks pass.

## Department of Homeland Security (DHS) / Section 508 Accessibility Connection

Accessibility smoke validation is included as part of release readiness. This does not claim full Section 508 certification, but it ensures basic accessibility checks are not treated as optional afterthoughts.

## Reliability Value

The release quality gate turns individual validation commands into a repeatable validation workflow. It helps replace ad hoc release judgment with documented, repeatable validation checks.

## Controlled Defect Validation

Controlled defect detection validation is available as an optional release-gate step by running this script with `-IncludeControlledDefectValidation`.

It is not enabled by default because it intentionally enables a defect mode, validates that the consistency checks catch the defect, and then restores normal behavior.
