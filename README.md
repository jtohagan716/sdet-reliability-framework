# SDET Reliability Framework

A reliability-focused Software Development Engineer in Test (SDET) project demonstrating modern software quality, Application Programming Interface (API) validation, observability, performance results, accessibility smoke validation, and release-readiness practices.

## Project Purpose

This project is not intended to be a complex business application.

It is a practice framework designed to demonstrate how a system can be validated, observed, measured, tested under lightweight load, checked for basic accessibility behavior, and evaluated through a repeatable release quality gate.

The project supports the following professional direction:

- Quality Assurance (QA) automation
- Software Development Engineer in Test (SDET)
- Application reliability
- Performance testing
- Federal healthcare platform validation
- Section 508-oriented accessibility awareness
- Continuous Integration / Continuous Delivery (CI/CD) quality gate thinking

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
- Accessibility scan validation
- release quality gate results
- versioned release documentation

## Release Progression

| Release | Capability |
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

## Technology Stack

- Python
- FastAPI
- Pytest
- Postman
- Newman
- Playwright
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
| /patients/9999 | Expected not-found lookup |
| /patients/abc | Expected invalid-input response |
| /metrics | Prometheus metrics endpoint |
| /patient-lookup | Simple user-facing page for accessibility smoke validation |

## Validation Layers

### Pytest

Pytest validates backend behavior, Application Programming Interface (API) logic, page structure, and script helper functions.

Run:

    python -m pytest

### Newman Application Programming Interface (API) Regression

Newman runs the Postman Application Programming Interface (API) regression collection from the command line.

Run:

    npm run postman:test

### Playwright Automation

Playwright validates browser-facing behavior, Application Programming Interface (API) workflows, and accessibility smoke checks.

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

### Release Quality Gate

The release quality gate script runs the major validation checks and generates release-readiness results.

Run:

    .\scripts\run_release_quality_gate.ps1

## Reports

Key generated reports include:

| Report | Purpose |
|---|---|
| reports/performance_baseline_v0.6.0.md | Initial performance baseline results |
| reports/lightweight_load_test_v0.7.0.md | Initial lightweight load test results |
| reports/accessibility_smoke_v0.8.0.md | Section 508-oriented accessibility smoke report |
| reports/release_quality_gate_v0.9.0.md | release quality gate results |
| reports/performance_baseline_quality_gate_v0.9.0.md | Quality-gate-specific performance baseline results |
| reports/lightweight_load_test_quality_gate_v0.9.0.md | Quality-gate-specific lightweight load test results |

## Documentation

Key documentation includes:

| Document | Purpose |
|---|---|
| docs/PROJECT_WALKTHROUGH.md | Reviewer-friendly explanation of the project |
| docs/RELEASE_QUALITY_GATES.md | Release quality gate documentation |
| docs/SECTION_508_ACCESSIBILITY.md | Section 508-oriented accessibility smoke validation |
| docs/ACCESSIBILITY_SCAN_VALIDATION.md | Accessibility scan validation documentation |
| docs/LIGHTWEIGHT_LOAD_TESTING.md | Lightweight load testing documentation |
| docs/PERFORMANCE_BASELINE.md | Performance baseline documentation |
| docs/METRICS_AND_PERFORMANCE_BASELINE.md | Metrics and baseline foundation |
| docs/REQUEST_ID_TRACEABILITY.md | Request identifier traceability |
| docs/DIAGNOSTIC_LOGGING.md | Diagnostic logging and request timing |

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

This project does not claim full Section 508 certification. It includes Section 508-oriented accessibility smoke validation that can be expanded later.

## Current Scope

This is a practice project.

It is designed to demonstrate modern quality engineering practices in a controlled, explainable environment. It is not intended to represent a full enterprise production system.

## Future Improvements

Planned or possible future improvements include:

- Kubernetes local deployment validation
- GitHub Actions quality gate expansion
- axe-core accessibility scanning
- performance threshold enforcement
- baseline comparison reports
- stronger security testing documentation
- Department of Homeland Security (DHS) Trusted Tester study alignment






