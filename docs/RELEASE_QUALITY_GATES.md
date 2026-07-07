# Release Quality Gates

## Purpose

The release quality gate provides a repeatable validation workflow for the SDET Reliability Framework.

It collects important project checks into one release-readiness script so that release decisions are based on documented validation results instead of ad hoc judgment.

Run the default release gate with:

    .\scripts\run_release_quality_gate.ps1

The script generates:

    reports/release_quality_gate_v1.9.0.md

## Current Release Gate Scope

The current release gate includes:

- dependency security validation
- Python syntax checks
- full Pytest regression suite
- Docker stack startup
- PostgreSQL schema validation
- PostgreSQL-backed patient lookup validation
- API-to-database consistency validation
- PostgreSQL query plan and index validation
- Newman API regression
- Playwright accessibility smoke validation
- full Playwright automation
- performance baseline results
- lightweight load test results
- local Docker/API smoke validation

## Release Gate Script

The main release gate script is:

    scripts/run_release_quality_gate.ps1

Default run:

    .\scripts\run_release_quality_gate.ps1

Run with optional controlled defect validation:

    .\scripts\run_release_quality_gate.ps1 -IncludeControlledDefectValidation

Controlled defect validation is optional because it intentionally enables a known defect mode, validates that the consistency checks detect it, and then restores normal behavior.

## Default Gate Steps

The default release gate currently runs the following checks.

| Gate | Purpose |
|---|---|
| Dependency security quality gate | Validates dependency health and audit posture |
| Python syntax check - FastAPI app | Confirms the API application file compiles |
| Python syntax check - performance baseline script | Confirms the performance baseline script compiles |
| Python syntax check - lightweight load test script | Confirms the lightweight load test script compiles |
| Full Pytest regression suite | Runs the Python regression suite |
| Start Docker stack | Builds and starts the local Docker Compose stack |
| PostgreSQL schema validation | Confirms expected database schema and deterministic seed data |
| PostgreSQL-backed patient lookup validation | Confirms the API can retrieve patient data from PostgreSQL |
| API-to-database consistency validation | Compares API results against direct PostgreSQL query results |
| PostgreSQL query plan and index validation | Confirms query plan evidence and expected index structure |
| Newman API regression | Runs the Postman API regression collection |
| Focused Section 508 accessibility smoke validation | Runs focused Playwright accessibility smoke checks |
| Full Playwright automation | Runs the full Playwright automation suite |
| Performance baseline results | Generates quality-gate-specific performance baseline output |
| Lightweight load test results | Generates quality-gate-specific lightweight load output |
| Local Docker/API smoke validation | Runs a combined Docker, API, Pytest, and Newman smoke check |

## Dependency Security Gate

Dependency security validation is handled by:

    scripts/validate_dependency_security.ps1

The release gate calls this script as part of release readiness.

The dependency security gate includes blocking and advisory checks.

### Blocking Dependency Checks

Blocking checks fail the dependency security gate if they fail.

| Check | Command |
|---|---|
| Python package dependency health | `python -m pip check` |
| Python vulnerability audit | `python -m pip_audit -r .\requirements.txt` |
| Node production/runtime audit | `npm audit --omit=dev --audit-level=high` |

### Advisory Dependency Check

The full Node audit is advisory:

    npm audit --audit-level=high

The full Node audit currently reports known transitive development/test-tooling findings through the Newman/Postman dependency chain.

The findings are documented and reviewed, but the release gate does not blindly run:

    npm audit fix --force

The forced fix is not applied because the audit output indicates that it would downgrade Newman in a breaking way.

## PostgreSQL Validation

The release gate includes several PostgreSQL-backed checks.

These checks validate that the API and database behavior remain aligned.

| Script | Purpose |
|---|---|
| `scripts/validate_postgresql_schema.ps1` | Validates schema and seed data |
| `scripts/validate_postgresql_patient_lookup.ps1` | Validates PostgreSQL-backed API lookup behavior |
| `scripts/validate_api_database_consistency.ps1` | Compares API output to direct database query output |
| `scripts/validate_patient_lookup_query_plan.ps1` | Validates query plan/index evidence |

These checks support backend reliability by validating not only API responses, but also the data behavior behind those responses.

## Controlled Defect Validation

Controlled defect validation is available through:

    scripts/validate_controlled_defect_detection.ps1

It can also be included in the release gate with:

    .\scripts\run_release_quality_gate.ps1 -IncludeControlledDefectValidation

This validation intentionally enables a known defect mode:

    PATIENT_LOOKUP_DEFECT_MODE=include_scheduled_last_visit

The script then verifies that API-to-database consistency validation detects the defect.

It restores normal behavior after the check.

This is not enabled by default because it intentionally mutates runtime behavior and recreates the API container.

## Generated Reports

The release gate generates a release-readiness report.

Current v1.9.0 report:

    reports/release_quality_gate_v1.9.0.md

The release gate also generates quality-gate-specific performance and load reports:

    reports/performance_baseline_quality_gate_v1.9.0.md
    reports/lightweight_load_test_quality_gate_v1.9.0.md

## Pass and Fail Behavior

Each gate step records:

- gate name
- command
- pass/fail status
- exit code
- duration in seconds

If any required gate fails, the release quality gate fails.

If all required gates pass, the release quality gate completes successfully.

Advisory findings inside the dependency security gate are documented for review but do not automatically fail the release gate unless they affect blocking checks.

## Release Decision Logic

A release should not be considered ready unless the required checks pass.

The release gate supports this decision process by making validation results explicit.

The gate helps answer:

- Did the API compile?
- Did the regression tests pass?
- Did the Docker stack start?
- Did PostgreSQL validation pass?
- Did API responses match expected database behavior?
- Did query/index validation pass?
- Did API regression checks pass?
- Did browser and accessibility smoke checks pass?
- Did performance and lightweight load checks complete?
- Did dependency security checks pass?
- Are advisory dependency findings documented?

## International Software Testing Qualifications Board (ISTQB) / Certified Tester Foundation Level (CTFL) Connection

This workflow supports release exit criteria and regression evidence.

It reinforces:

- regression testing
- confirmation testing
- exit criteria
- test completion criteria
- risk-based release decisions
- documented test results

## Department of Homeland Security (DHS) / Section 508 Accessibility Connection

Accessibility smoke validation is included as part of release readiness.

This project does not claim full Section 508 certification.

The accessibility checks are intended to ensure that basic accessibility concerns are included in the release workflow rather than treated as an afterthought.

## Reliability Value

The release quality gate turns individual validation commands into one repeatable workflow.

That matters because reliable systems require repeatable validation.

The gate helps reduce the risk of:

- missing a regression step
- relying on memory
- treating database validation as separate from API validation
- ignoring dependency risk
- shipping without documented release evidence

## Current Scope

This release gate is designed for a practice-scale reliability validation framework.

It is not a full enterprise release-management system.

It demonstrates practical release validation behavior using synthetic data and local/CI-friendly tooling.

## Future Improvements

Potential future improvements include:

- add dependency security validation to GitHub Actions
- add Dependabot configuration
- add Software Bill of Materials generation
- add accepted-risk review dates for advisory dependency findings
- add stricter performance thresholds
- add trend comparison against prior baselines
- add larger PostgreSQL query plan comparison runs
- add optional release profiles for fast, standard, and full validation
