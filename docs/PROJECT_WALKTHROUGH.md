# Project Walkthrough

## Project Purpose

This project is a reliability-focused Software Development Engineer in Test (SDET) project.

The goal is not to build a complex business application. The goal is to demonstrate modern software quality practices around Application Programming Interface (API) validation, automated regression testing, Docker-based local runtime validation, diagnostic logging, request tracing, Prometheus metrics, performance results, lightweight load testing, PostgreSQL schema validation, Section 508-oriented accessibility smoke validation, and release quality gates.

## Professional Framing

This project is designed to show how an experienced production systems professional can modernize into reliability-focused Quality Assurance (QA), Software Development Engineer in Test (SDET), performance testing, and application reliability work.

The project demonstrates the ability to:

- validate Application Programming Interface (API) behavior
- automate regression checks
- run a local Docker-based system
- collect diagnostic logging
- trace requests with request identifiers
- expose Prometheus metrics
- avoid high-cardinality metric labels
- generate performance baseline results
- run lightweight load testing
- include Section 508-oriented accessibility smoke validation
- organize checks into a repeatable release quality gate
- document release-readiness results

## Release Progression

| Release | Capability Added |
|---|---|
| v0.2.0 | REST Application Programming Interface (API) validation and smoke testing |
| v0.3.0 | Diagnostic logging and request timing |
| v0.4.0 | Request identifier traceability |
| v0.5.0 | Prometheus metrics and observability signals |
| v0.6.0 | performance baseline results |
| v0.7.0 | Lightweight load testing |
| v0.8.0 | Section 508-oriented accessibility smoke validation |
| v0.9.0 | release quality gate results |
| v1.0.0 | Reliability Software Development Engineer in Test (SDET) project baseline |
| v1.1.0 | Continuous Integration (CI) quality gate expansion |
| v1.2.0 | Application Programming Interface (API) contract validation |
| v1.3.0 | Accessibility scan validation |
| v1.4.0 | PostgreSQL schema and synthetic seed data validation |
| v1.5.0 | PostgreSQL-backed patient lookup validation |

## Main Validation Layers

### Pytest Regression Testing

Pytest validates backend behavior and Application Programming Interface (API) logic.

Purpose:

- confirm expected endpoint behavior
- catch regressions
- validate synthetic patient scenarios
- confirm generated pages return expected structure

### Newman Application Programming Interface (API) Regression

Newman runs the Postman Application Programming Interface (API) regression collection.

Purpose:

- validate Application Programming Interface (API) contracts
- confirm status codes and response expectations
- provide repeatable command-line Application Programming Interface (API) checks

### Playwright Automation

Playwright validates browser-facing and workflow behavior.

Purpose:

- validate user interface behavior
- validate Application Programming Interface (API)-driven workflows
- validate accessibility smoke checks
- confirm that user-facing behavior works from an external test runner

### Docker Smoke Validation

Docker Compose starts the local system.

Purpose:

- confirm the service can run in a containerized local environment
- validate health checks
- run key end-to-end checks against the running service

### Prometheus Metrics

Prometheus metrics expose measurable reliability signals.

Purpose:

- count requests
- measure request duration
- track patient lookup outcomes
- support future dashboarding and alerting

### Performance Baseline

The performance baseline captures normal local response-time and error-rate behavior.

Purpose:

- establish a known-good reference point
- capture count, pass/fail, error rate, average response time, minimum, maximum, and p95 response time
- support future performance comparison

### Lightweight Load Testing

The lightweight load test applies a weighted traffic mix with concurrency.

Purpose:

- simulate more realistic local traffic
- capture throughput
- capture p95 and p99 response time
- identify tail-latency outliers
- confirm expected status codes under small concurrent load

### Section 508-Oriented Accessibility Smoke Validation

The accessibility smoke validation checks basic accessible structure and keyboard-friendly behavior.

Purpose:

- validate page title and heading
- validate accessible input labels
- validate accessible button role and name
- validate keyboard reachability
- validate live result-region feedback

This does not claim full Section 508 certification. It is a smoke validation layer that can be expanded later.


### API Contract Validation

API contract validation checks that selected Application Programming Interface (API) responses keep the expected structure, required fields, data types, and error formats.

Purpose:

- validate stable response fields
- validate expected data types
- validate date and datetime formatting
- validate expected error response structure
- detect response-shape changes that status-code checks may miss

Test file:

    tests/test_api_contract_validation.py


### Accessibility Scan Validation

Accessibility scan validation uses axe-core through Playwright to scan the rendered Patient Lookup page for automatically detectable accessibility violations.

Purpose:

- scan the rendered page with automated accessibility rules
- supplement page-specific accessibility smoke checks
- validate selected WCAG rule tags
- keep accessibility validation in the automated test path
- provide a repeatable check that can expand as more pages are added

Test file:

    tests/ui/patient_lookup_axe_accessibility.spec.ts

### PostgreSQL Schema Validation

PostgreSQL schema validation checks that the local database foundation is repeatable, relationally valid, and ready to support future API/database consistency testing.

Purpose:

- validate the PostgreSQL container is running
- confirm the expected database tables exist
- confirm deterministic synthetic seed data loaded correctly
- validate many-to-many join behavior through the encounter_diagnoses bridge table
- validate left join behavior for patients with and without encounters
- support future query plan and index performance comparison

Validation script:

    scripts/validate_postgresql_schema.ps1

Documentation:

    docs/POSTGRESQL_SCHEMA.md

Report:

    reports/postgresql_schema_seed_data_v1.4.0.md

### Release Quality Gate

The release quality gate runs major validation checks and generates results before release.

Purpose:

- replace ad hoc release judgment with repeatable validation
- organize regression, smoke, performance, accessibility, and Application Programming Interface (API) checks
- generate a release-readiness report

## International Software Testing Qualifications Board (ISTQB) / Certified Tester Foundation Level (CTFL) Alignment

This project reinforces the following testing concepts:

- test levels
- test types
- regression testing
- confirmation testing
- acceptance criteria
- exit criteria
- test completion criteria
- test results
- risk-based testing
- defect prevention

## Department of Homeland Security (DHS) / Section 508 Alignment

This project reinforces the following accessibility concepts:

- accessibility should be tested before release
- user-facing controls need accessible labels
- keyboard interaction matters
- page structure matters
- automated smoke validation is useful but does not replace full formal Section 508 testing
- accessibility should be part of release readiness, not an afterthought

## How to Run the Main Quality Gate

Start Docker Desktop first.

Then run:

    .\scripts\run_release_quality_gate.ps1

Expected result:

    Release quality gate completed successfully.

Report generated:

    reports/release_quality_gate_v0.9.0.md

## Current Scope

This is a practice project. It does not claim to be an enterprise production system.

It is designed to demonstrate modern quality engineering practices in a controlled, explainable environment.

## Future Improvements

Possible future work includes:

- Kubernetes local deployment validation
- GitHub Actions quality gate expansion
- axe-core accessibility scanning
- performance threshold enforcement
- baseline comparison reports
- stronger security testing documentation
- Department of Homeland Security (DHS) Trusted Tester study alignment







