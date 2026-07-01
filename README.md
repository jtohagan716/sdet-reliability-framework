# SDET Reliability Framework

[![SDET Reliability Framework CI](https://github.com/jtohagan716/sdet-reliability-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/jtohagan716/sdet-reliability-framework/actions/workflows/ci.yml)

## Overview

The **SDET Reliability Framework** is a Quality Engineering and reliability-focused portfolio project that demonstrates automated testing, API validation, observability, performance signal tracking, and release-readiness evidence.

The project combines modern QA automation practices with production-systems thinking. It is designed to show how automated tests, health checks, metrics, dashboards, API validation, CI execution, and release reporting can work together to support better software release decisions.

This project reflects a practical engineering mindset:

> Quality is not only whether tests pass. Quality also includes whether the system is healthy, observable, reliable, testable, and ready to release.

---

## Project Objectives

This framework demonstrates how to:

- Build automated validation around backend service health.
- Run Python/Pytest-based reliability and regression checks.
- Run Playwright automation for API, workflow, observability, and performance validation.
- Validate REST API behavior using Postman and Newman.
- Expose runtime metrics for Prometheus.
- Visualize service health through Grafana.
- Use Docker Compose to run a repeatable local reliability stack.
- Use GitHub Actions for CI-based validation.
- Produce release-readiness evidence for technical review.
- Document architecture, engineering decisions, validation evidence, and visual proof.

---

## Technology Stack

| Area | Tools / Technologies |
|---|---|
| Backend Service | FastAPI, Python |
| Python Testing | Pytest |
| Browser / API Automation | Playwright |
| API Testing | Postman, Newman |
| Containerization | Docker, Docker Compose |
| Observability | Prometheus, Grafana |
| CI/CD Validation | GitHub Actions |
| Reporting | Release-readiness report, Newman JUnit-style XML report |
| Documentation | Markdown, Architecture Decision Records, Wiki |
| Version Control | Git, GitHub |

---

## Architecture Summary

The framework uses a small but realistic reliability stack:

```text
Developer / CI
     |
     v
Automated Tests
  - Pytest
  - Playwright
  - Postman/Newman
     |
     v
FastAPI Backend Service
  - /health
  - /metrics
  - /openapi.json
     |
     v
Observability Layer
  - Prometheus
  - Grafana
     |
     v
Release-Readiness Evidence
  - Test results
  - Metrics evidence
  - API validation evidence
  - Visual evidence
  - Release recommendation
```

The backend service exposes health, metrics, and OpenAPI endpoints. Automated validation checks those endpoints and produces evidence that can support release decisions.

---

## Quality and Reliability Pipeline

The project demonstrates several layers of validation:

1. **Backend health validation**
   - Confirms the service is reachable and reports healthy status.

2. **REST API validation**
   - Confirms expected HTTP status codes, response fields, OpenAPI availability, metrics availability, and controlled error behavior.

3. **Automated Python validation**
   - Runs Pytest checks for API, security, workflow, payload, FHIR, regression, and reliability scenarios.

4. **Playwright automation**
   - Runs API health checks, synthetic behavior checks, mocked backend failure scenarios, network inspection, and performance trend validation.

5. **Observability validation**
   - Confirms Prometheus metrics are exposed and Grafana can visualize runtime behavior.

6. **Release-readiness reporting**
   - Summarizes validation results, failed checks, risk level, release status, and recommendation.

7. **CI validation**
   - GitHub Actions validates the stack, runs automated tests, and provides visible build status.

---

## Core Components

### FastAPI Backend

The backend service provides API endpoints used for health, metrics, OpenAPI contract visibility, and reliability validation.

Key endpoints include:

```text
GET /health
GET /metrics
GET /openapi.json
```

---

### Python / Pytest Validation

Executes Python-based validation across API, regression, security, workflow, payload, and performance-related test areas.

Example validation areas include:

* API contract validation
* Failure signature checks
* Synthetic API journeys
* Validation workflows
* Payload correlation
* Performance checks
* Canary health and trend analysis
* Security context validation
* JWT validation
* Operational decision logic
* Workflow validation

---

### Playwright Automation

Playwright is used for modern automation coverage beyond traditional UI-only testing.

The suite includes validation for:

- API health canaries
- FastAPI health checks
- mocked backend failure behavior
- security workflows
- network inspection
- observability validation
- Prometheus validation
- performance trend reporting

---

### Postman REST API Testing

The framework includes a Postman collection for REST API and backend service validation.

The collection covers:

- backend health checks
- Prometheus metrics availability
- OpenAPI contract validation
- HTTP status-code assertions
- response-field validation
- response-time checks
- negative API testing
- command-line execution with Newman
- JUnit-style XML report generation

Postman API testing evidence is documented in:

[`docs/POSTMAN_API_TESTING.md`](docs/POSTMAN_API_TESTING.md)

The Postman collection and environment are located in:

```text
postman/SDET_Reliability_Framework.postman_collection.json
postman/SDET_Reliability_Local.postman_environment.json
```

The Newman report output is generated at:

```text
reports/postman-newman-results.xml
```

---

### Docker Compose Reliability Stack

The local stack includes:

```text
FastAPI service
Prometheus
Grafana
```

This allows the application, metrics, and dashboard components to run together in a repeatable local environment.

---

### Prometheus Metrics

The API exposes Prometheus-compatible metrics through:

```text
GET /metrics
```

This supports service observability and gives the test framework measurable runtime signals.

---

### Grafana Dashboard

Grafana is used to visualize service behavior and demonstrate operational monitoring concepts.

The visual evidence documentation includes screenshots showing the Grafana dashboard and Prometheus target health.

---

### Release-Readiness Report

The framework includes a release-readiness report that summarizes validation evidence and supports release decisions.

The report helps answer:

- Did the validation checks pass?
- Were any failures detected?
- What is the risk level?
- Is the release recommended?
- What evidence supports that recommendation?

Release report:

[`reports/release_readiness_report.txt`](reports/release_readiness_report.txt)

---

## Portfolio Evidence

This project includes supporting evidence for technical review:

| Evidence | Link |
|---|---|
| Local validation evidence | [`docs/LOCAL_VALIDATION_EVIDENCE.md`](docs/LOCAL_VALIDATION_EVIDENCE.md) |
| Visual evidence | [`docs/VISUAL_EVIDENCE.md`](docs/VISUAL_EVIDENCE.md) |
| Postman API testing evidence | [`docs/POSTMAN_API_TESTING.md`](docs/POSTMAN_API_TESTING.md) |
| System architecture | [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md) |
| Engineering decisions | [`docs/ENGINEERING_DECISIONS.md`](docs/ENGINEERING_DECISIONS.md) |
| Architecture Decision Records | [`docs/adr/`](docs/adr/) |
| Release-readiness report | [`reports/release_readiness_report.txt`](reports/release_readiness_report.txt) |
| GitHub Actions CI | [GitHub Actions](https://github.com/jtohagan716/sdet-reliability-framework/actions) |

---

## Local Validation Evidence

The project has been validated locally with:

```text
Docker stack running successfully
FastAPI health endpoint responding
Prometheus metrics endpoint available
Prometheus server healthy
Python/Pytest test suite passing
Playwright automation suite passing
Postman/Newman API validation passing
Newman XML report generated
```

Documented evidence:

```text
.
├── api_service/          FastAPI application
├── docs/                 Architecture and engineering documentation
├── reports/              Generated reports and evidence
├── scripts/              Release assessment and automation utilities
├── tests/
│   ├── api/              API validation tests
│   ├── baselines/        Baseline and reporting tests
│   ├── validation/       Validation and workflow tests
│   ├── payloads/         Payload correlation and translation tests
│   ├── performance/      Performance-related tests
│   ├── regression/       Reliability and regression tests
│   ├── security/         Security and JWT validation tests
│   ├── ui/               Playwright tests
│   └── workflows/        Workflow validation tests
├── docker-compose.yml
├── prometheus.yml
└── README.md
```

---

## Visual Evidence

Visual evidence includes screenshots for:

- Docker stack running
- GitHub repository structure
- GitHub commit history
- Grafana dashboard
- Prometheus target health

Documented evidence:

[`docs/VISUAL_EVIDENCE.md`](docs/VISUAL_EVIDENCE.md)

---

## Running the Project Locally

### 1. Clone the repository

```powershell
git clone https://github.com/jtohagan716/sdet-reliability-framework.git
cd sdet-reliability-framework
```

### 2. Start the Docker stack

```powershell
docker compose up -d
```

### 3. Confirm containers are running

```powershell
docker ps
```

### 4. Validate the API health endpoint

```powershell
Invoke-RestMethod http://localhost:8000/health
```

### 5. Validate metrics

```powershell
Invoke-WebRequest http://localhost:8000/metrics
```

### 6. Access observability tools

```text
FastAPI API:  http://localhost:8000
Prometheus:   http://localhost:9090
Grafana:      http://localhost:3000
```

---

## Running Tests

### Python / Pytest

```powershell
python -m pytest -q
```

### Playwright

```powershell
npx playwright test
```

### Postman / Newman API Tests

Run the Postman collection from the command line:

```powershell
npm run postman:test
```

Run the Postman collection and generate a JUnit-style XML report:

```powershell
npm run postman:test:report
```

Expected successful result:

```text
requests: 4 executed, 0 failed
test-scripts: 4 executed, 0 failed
assertions: 11 executed, 0 failed
```

---

## Postman API Test Coverage

| Request | Validation |
|---|---|
| `GET /health` | Confirms the backend service is reachable and reports `UP` status |
| `GET /metrics` | Confirms Prometheus-compatible metrics are exposed |
| `GET /openapi.json` | Confirms the FastAPI OpenAPI contract is available |
| `GET /invalid-endpoint` | Confirms invalid routes return controlled `404` responses |

This demonstrates practical REST API and backend service validation using Postman, Newman, environments, assertions, and report output.

---

## GitHub Actions CI

The repository includes GitHub Actions validation for:

- Docker build validation
- Python reliability tests
- performance gate execution
- Playwright automation tests
- API health validation
- observability-related checks

The CI badge at the top of this README provides quick visibility into the current validation status.

---

## Project Structure

```text
sdet-reliability-framework/
├── .github/
│   └── workflows/
│       └── ci.yml
├── api_service/
│   └── app.py
├── config/
├── docs/
│   ├── adr/
│   ├── images/
│   ├── ENGINEERING_DECISIONS.md
│   ├── LOCAL_VALIDATION_EVIDENCE.md
│   ├── POSTMAN_API_TESTING.md
│   ├── SYSTEM_ARCHITECTURE.md
│   └── VISUAL_EVIDENCE.md
├── postman/
│   ├── SDET_Reliability_Framework.postman_collection.json
│   └── SDET_Reliability_Local.postman_environment.json
├── reports/
│   ├── postman-newman-results.xml
│   └── release_readiness_report.txt
├── scripts/
├── tests/
├── docker-compose.yml
├── package.json
├── package-lock.json
├── playwright.config.ts
├── README.md
└── requirements.txt
```

---

## Engineering Decisions

The project includes Architecture Decision Records to explain key design decisions.

Examples include:

- Using Docker Compose for the local reliability stack
- Using a quality signal model
- Separating release assessment from test execution

Architecture Decision Records:

[`docs/adr/`](docs/adr/)

---

## Current Status

Current project status:

```text
Docker stack: validated
FastAPI health endpoint: validated
Prometheus metrics endpoint: validated
Grafana dashboard evidence: documented
Python/Pytest suite: validated
Playwright suite: validated
Postman/Newman API suite: validated
Newman XML report: generated
GitHub Actions CI: configured
Release-readiness report: available
Architecture documentation: available
Visual evidence: available
ADR documentation: available
```

---

## Professional Relevance

This project demonstrates practical skills relevant to roles such as:

- QA Automation Engineer
- Quality Engineer
- SDET
- Test Automation Engineer
- Application Support Engineer
- Production Support Engineer
- Performance Test Engineer
- Reliability-focused QA Engineer
- Healthcare IT Quality Analyst
- Cross-Functional Test Engineer

It demonstrates experience with:

- automated testing
- REST API testing
- backend service validation
- Postman and Newman
- Python/Pytest
- Playwright
- Docker
- CI validation
- Prometheus metrics
- Grafana observability
- release-readiness reporting
- defect and risk evidence
- system health validation
- repeatable test execution

---

## Career Context

This project was built to connect production systems experience with modern Quality Engineering practices.

It reflects a background in:

- production troubleshooting
- performance testing
- system validation
- backend service behavior
- log and evidence collection
- defect triage
- release support
- operational risk assessment
- healthcare IT reliability

The framework demonstrates how those same reliability and validation concepts can be applied using modern QA automation and observability tools.

---

## Future Enhancements

Potential future improvements include:

- CI integration for Postman/Newman execution
- additional REST API negative tests
- authentication and authorization API testing
- expanded OpenAPI contract validation
- dependency/security scanning
- expanded Grafana dashboard examples
- automated release report artifact upload
- additional NIST-aligned security validation documentation
- cross-functional change validation testing
- cloud/on-prem change validation simulation

---

## Summary

The SDET Reliability Framework demonstrates how modern QA automation, backend API validation, observability, and release-readiness evidence can work together.

It is designed to show more than test execution. It shows a disciplined validation workflow:

```text
Run the system
Validate the API
Run automated tests
Check metrics
Observe behavior
Generate evidence
Assess release readiness
Document decisions
```

This project represents a practical bridge between production systems experience and modern Quality Engineering, SDET, reliability validation, and application support practices.
