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
- Validate synthetic domain API behavior using Pytest and Postman/Newman.
- Expose runtime metrics for Prometheus.
- Visualize service health through Grafana.
- Use Docker Compose to run a repeatable local reliability stack.
- Use GitHub Actions for CI-based validation.
- Produce release-readiness evidence for technical review.
- Document architecture, engineering decisions, validation evidence, API testing strategy, and visual proof.

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
  - /patients/{patient_id}
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

The backend service exposes health, metrics, OpenAPI, and synthetic domain API endpoints. Automated validation checks those endpoints and produces evidence that can support release decisions.

---

## Quality and Reliability Pipeline

The project demonstrates several layers of validation:

1. **Backend health validation**
   - Confirms the service is reachable and reports healthy status.

2. **REST API validation**
   - Confirms expected HTTP status codes, response fields, OpenAPI availability, metrics availability, controlled error behavior, path-parameter validation, unsupported-method handling, and synthetic domain API behavior.

3. **Automated Python validation**
   - Runs Pytest checks for API, security, workflow, payload, FHIR, regression, synthetic REST API, and reliability scenarios.

4. **Playwright automation**
   - Runs API health checks, synthetic behavior checks, mocked backend failure scenarios, network inspection, and performance trend validation.

5. **Observability validation**
   - Confirms Prometheus metrics are exposed and Grafana can visualize runtime behavior.

6. **Release-readiness reporting**
   - Summarizes validation results, failed checks, risk level, release status, and recommendation.

7. **CI validation**
   - GitHub Actions validates the stack, runs automated tests, uploads Newman API evidence, and provides visible build status.

---

## Core Components

### FastAPI Backend

The backend service provides API endpoints used for health, metrics, OpenAPI contract visibility, synthetic domain behavior, and reliability validation.

Key endpoints include:

```text
GET /health
GET /metrics
GET /openapi.json
GET /patients/{patient_id}
```

The synthetic patient endpoint uses fictional test data only and supports deeper REST API validation, including:

- valid resource retrieval
- missing-resource `404` behavior
- invalid path-parameter `422` validation
- unsupported-method `405` handling
- OpenAPI contract visibility
- response-field validation
- sensitive-data exclusion checks

---

### Python / Pytest Validation

The Python test suite validates backend behavior, reliability logic, payload handling, security-oriented workflows, regression scenarios, synthetic REST API behavior, and release-readiness conditions.

Example validation areas include:

- API behavior
- synthetic patient API validation
- positive and negative REST API scenarios
- payload validation
- security workflow checks
- backend failure behavior
- FHIR-oriented test data
- performance and operational decision logic
- release-readiness support

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
- synthetic patient API validation
- path-parameter validation
- unsupported-method handling
- sensitive-data exclusion checks
- command-line execution with Newman
- JUnit-style XML report generation

Postman API testing evidence is documented in:

[`docs/POSTMAN_API_TESTING.md`](docs/POSTMAN_API_TESTING.md)

Additional REST API testing artifacts include:

- [`docs/REST_API_TESTING_STRATEGY.md`](docs/REST_API_TESTING_STRATEGY.md)
- [`docs/API_TEST_CASE_MATRIX.md`](docs/API_TEST_CASE_MATRIX.md)
- [`docs/REST_API_DEPTH_IMPLEMENTATION_NOTES.md`](docs/REST_API_DEPTH_IMPLEMENTATION_NOTES.md)

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

### REST API Testing Depth

The project now includes a synthetic domain API endpoint:

```text
GET /patients/{patient_id}
```

This endpoint demonstrates more realistic backend API testing beyond basic health checks.

Validated scenarios include:

| Scenario | Expected Result |
|---|---|
| `GET /patients/1001` | `200 OK` with expected synthetic active patient |
| `GET /patients/1002` | `200 OK` with expected synthetic inactive patient |
| `GET /patients/9999` | `404 Not Found` for unknown synthetic patient |
| `GET /patients/abc` | `422 Validation Error` for invalid path parameter |
| `POST /patients/1001` | `405 Method Not Allowed` for unsupported method |
| `GET /openapi.json` | Confirms `/patients/{patient_id}` is documented |

This coverage demonstrates:

- positive REST API testing
- negative REST API testing
- path-parameter validation
- response-body validation
- OpenAPI contract awareness
- method-boundary validation
- response-time threshold checks
- sensitive-data exclusion
- Pytest API automation
- Postman/Newman API automation
- CI-ready API evidence

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
| REST API testing strategy | [`docs/REST_API_TESTING_STRATEGY.md`](docs/REST_API_TESTING_STRATEGY.md) |
| API test case matrix | [`docs/API_TEST_CASE_MATRIX.md`](docs/API_TEST_CASE_MATRIX.md) |
| REST API depth implementation notes | [`docs/REST_API_DEPTH_IMPLEMENTATION_NOTES.md`](docs/REST_API_DEPTH_IMPLEMENTATION_NOTES.md) |
| CI pipeline overview | [`docs/CI_PIPELINE_OVERVIEW.md`](docs/CI_PIPELINE_OVERVIEW.md) |
| Security policy | [`SECURITY.md`](SECURITY.md) |
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
Synthetic patient REST API endpoint responding
Prometheus metrics endpoint available
Prometheus server healthy
Python/Pytest test suite passing
Synthetic REST API Pytest coverage passing
Playwright automation suite passing
Postman/Newman API validation passing
Newman XML report generated
```

Documented evidence:

- [`docs/LOCAL_VALIDATION_EVIDENCE.md`](docs/LOCAL_VALIDATION_EVIDENCE.md)
- [CI Pipeline Overview](docs/CI_PIPELINE_OVERVIEW.md)
- [REST API Depth Implementation Notes](docs/REST_API_DEPTH_IMPLEMENTATION_NOTES.md)
- [API Failure Triage Guide](docs/API_FAILURE_TRIAGE_GUIDE.md)
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

### 5. Validate the synthetic patient API endpoint

```powershell
Invoke-RestMethod http://localhost:8000/patients/1001
```

### 6. Validate metrics

```powershell
Invoke-WebRequest http://localhost:8000/metrics
```

### 7. Access observability tools

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

Run the focused synthetic REST API test coverage:

```powershell
python -m pytest tests\test_synthetic_patient_api.py -q
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
requests: 10 executed, 0 failed
test-scripts: 10 executed, 0 failed
assertions: 37 executed, 0 failed
```

---

### CI-Integrated Postman/Newman API Validation

The framework runs Postman/Newman REST API validation in GitHub Actions as part of the automated CI workflow.

The CI pipeline:

- starts the Docker Compose reliability stack
- waits for the FastAPI service health check to pass
- runs the Postman collection with Newman
- generates a JUnit-style XML report
- uploads the Newman report as a GitHub Actions artifact
- continues into the Playwright automation suite

This demonstrates repeatable backend API validation, CI-based quality gates, and downloadable test evidence.

## Postman API Test Coverage

| Request | Validation |
|---|---|
| `GET /health` | Confirms the backend service is reachable and reports `UP` status |
| `GET /metrics` | Confirms Prometheus-compatible metrics are exposed |
| `GET /openapi.json` | Confirms the FastAPI OpenAPI contract is available |
| `GET /invalid-endpoint` | Confirms invalid routes return controlled `404` responses |
| `GET /patients/1001` | Confirms a valid synthetic patient returns `200 OK` with expected response fields |
| `GET /patients/1002` | Confirms a second valid synthetic patient returns distinct expected data |
| `GET /patients/9999` | Confirms an unknown synthetic patient returns controlled `404` behavior |
| `GET /patients/abc` | Confirms invalid path-parameter input returns `422` validation behavior |
| `POST /patients/1001` | Confirms unsupported methods return `405 Method Not Allowed` |
| `GET /openapi.json` | Confirms `/patients/{patient_id}` is documented in the OpenAPI contract |

This demonstrates practical REST API and backend service validation using Postman, Newman, environments, assertions, response-time checks, negative testing, contract validation, and report output.

---

## GitHub Actions CI

The repository includes GitHub Actions validation for:

- Docker build validation
- Python reliability tests
- synthetic REST API Pytest validation
- performance gate execution
- Postman/Newman REST API validation
- Newman XML artifact upload
- Playwright automation tests
- API health validation
- OpenAPI contract validation
- observability-related checks

The CI badge at the top of this README provides quick visibility into the current validation status.

---

## Project Structure

```text
sdet-reliability-framework/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   │   └── ci.yml
│   └── pull_request_template.md
├── api_service/
│   └── app.py
├── config/
├── docs/
│   ├── adr/
│   ├── images/
│   ├── API_TEST_CASE_MATRIX.md
│   ├── CI_PIPELINE_OVERVIEW.md
│   ├── ENGINEERING_DECISIONS.md
│   ├── LOCAL_VALIDATION_EVIDENCE.md
│   ├── POSTMAN_API_TESTING.md
│   ├── REST_API_DEPTH_IMPLEMENTATION_NOTES.md
│   ├── REST_API_TESTING_STRATEGY.md
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
├── SECURITY.md
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
Synthetic patient REST API endpoint: validated
Prometheus metrics endpoint: validated
Grafana dashboard evidence: documented
Python/Pytest suite: validated
Synthetic REST API Pytest coverage: validated
Playwright suite: validated
Postman/Newman API suite: validated
Postman/Newman coverage: 10 requests / 37 assertions
Newman XML report: generated
GitHub Actions CI: configured and passing
Newman CI artifact upload: configured
Release-readiness report: available
REST API strategy documentation: available
API test case matrix: available
REST API implementation notes: available
Architecture documentation: available
Visual evidence: available
ADR documentation: available
Security policy: available
Pull request checklist: available
Issue templates: available
```

---

## Professional Relevance

This project demonstrates practical skills relevant to roles such as:

- QA Automation Engineer
- Quality Engineer
- SDET
- Backend API Test Engineer
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
- synthetic domain API testing
- positive and negative API testing
- OpenAPI contract awareness
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

- authentication and authorization API testing
- role-based API validation
- expanded OpenAPI contract validation
- additional REST API negative tests for request bodies and headers
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
