# SDET Reliability Framework

[![SDET Reliability Framework CI](https://github.com/jtohagan716/sdet-reliability-framework/actions/workflows/ci.yml/badge.svg)](https://github.com/jtohagan716/sdet-reliability-framework/actions/workflows/ci.yml)

> A modern Quality Engineering platform demonstrating automated testing, observability, release assessment, and evidence-driven deployment decisions.
---

## Overview

The **SDET Reliability Framework** is a portfolio project that demonstrates how modern Quality Engineering extends beyond automated testing.

The framework combines UI automation, API validation, runtime health checks, observability, CI/CD concepts, performance trend analysis, and release assessment into a single quality pipeline that determines whether an application is ready for production deployment.

Rather than treating testing as an isolated pass/fail activity, the framework collects quality evidence from multiple sources and produces release recommendations based on that evidence.

The project is designed to show practical skills in:

* Automated testing
* Reliability engineering
* Runtime health validation
* Observability
* Performance signal analysis
* Security workflow validation
* Evidence-based release decisions

---

## Objectives

* Demonstrate modern Quality Engineering practices
* Integrate automated testing into a repeatable validation workflow
* Validate runtime health and observability signals
* Standardize quality evidence across multiple test sources
* Support evidence-driven release assessment
* Generate release readiness reports
* Show deterministic, reproducible validation behavior

---

## Technology Stack

| Area             | Technology              |
| ---------------- | ----------------------- |
| Language         | Python                  |
| API              | FastAPI                 |
| UI Automation    | Playwright              |
| API Testing      | Pytest / Playwright     |
| Containerization | Docker / Docker Compose |
| CI/CD            | GitHub Actions          |
| Monitoring       | Prometheus              |
| Dashboards       | Grafana                 |
| Version Control  | Git / GitHub            |

---

## High-Level Architecture

```text
                    GitHub Actions
                           │
                           ▼
                  Build & Execute Tests
                           │
         ┌─────────────────┴─────────────────┐
         │                                   │
         ▼                                   ▼
 Playwright Tests                  Runtime Health Checks
         │                                   │
         └───────────────┬───────────────────┘
                         ▼
                  QualitySignal Model
                         ▼
                 ReleaseAssessment
                         ▼
             Release Readiness Report
```

---

## Quality Pipeline

```text
Application
    ↓
Automated Testing
    ↓
Runtime Validation
    ↓
Observability Validation
    ↓
QualitySignal
    ↓
ReleaseAssessment
    ↓
Release Recommendation
```

The framework is intended to answer questions such as:

* Is the application running?
* Are the health endpoints responding correctly?
* Are metrics being exported?
* Are automated tests passing?
* Are security workflows behaving correctly?
* Are performance signals stable, improving, or degrading?
* Is the release ready, risky, or blocked?

---

## Core Components

### FastAPI

Provides the application under test.

Current endpoints include:

* `/health`
* `/metrics`

The `/health` endpoint reports application availability.

The `/metrics` endpoint exports Prometheus-compatible runtime and application metrics.

---

### Playwright

Executes browser-based and API-driven validation.

Current Playwright coverage includes:

* API health canary checks
* FastAPI health validation
* Synthetic canary validation
* Mocked backend failure simulation
* End-to-end security workflow validation
* Network inspection
* Performance baseline capture
* Performance history reporting
* Performance trend reporting

Test results are exported as structured evidence and used to support release assessment.

---

### Pytest

Executes Python-based validation across API, regression, security, workflow, payload, FHIR, and performance-related test areas.

Current Python test coverage includes:

* API contract validation
* Failure signature checks
* Synthetic API journeys
* FHIR validation workflows
* Payload correlation
* Performance checks
* Canary health and trend analysis
* Security context validation
* JWT validation
* Operational decision logic
* Workflow validation

---

### Docker

Provides consistent local execution across framework components.

The local stack includes:

* FastAPI application container
* Prometheus container
* Grafana container

Docker support allows the framework to run in a reproducible environment instead of depending only on local machine configuration.

---

### Prometheus

Collects application and runtime metrics.

Prometheus is used to validate that the application is exporting observable signals that can support operational and release-readiness decisions.

---

### Grafana

Visualizes operational metrics and system health.

Grafana supports dashboard-driven review of runtime behavior and observability signals.

---

### QualitySignal

A standardized quality evidence model.

Each evidence provider returns a `QualitySignal`, allowing the release engine to evaluate multiple technologies using a common interface.

Current evidence providers include:

* Runtime Health
* Playwright Observability

Additional providers are planned.

---

### ReleaseAssessment

Evaluates collected quality signals and produces a release decision.

The release assessment calculates:

* Total checks
* Failed checks
* Risk level
* Overall status
* Release recommendation

Release recommendations are based on evidence rather than assumptions.

---

## Validation Evidence

Recent local validation confirmed that the framework runs successfully and produces quality evidence across the local reliability stack.

Validation evidence includes:

* Docker stack running successfully
* FastAPI container reporting healthy status
* `/health` endpoint returning `UP`
* `/metrics` endpoint exporting Prometheus metrics
* Prometheus server reporting healthy status
* Grafana container running
* Python test suite passing
* Playwright test suite passing

Evidence documents:

* [`docs/LOCAL_VALIDATION_EVIDENCE.md`](docs/LOCAL_VALIDATION_EVIDENCE.md)
* [`reports/release_readiness_report.txt`](reports/release_readiness_report.txt)

Recent validation results:

```text
Python tests:     180 passed
Playwright tests: 87 passed
API health:       UP
Prometheus:       Healthy
Overall result:   PASS
```

---

## Portfolio Evidence

This repository includes supporting evidence that demonstrates the framework running as a real local reliability and quality engineering stack.

* [`docs/LOCAL_VALIDATION_EVIDENCE.md`](docs/LOCAL_VALIDATION_EVIDENCE.md)
  Documents local validation results, including Docker stack health, API health, metrics validation, Prometheus health, Python test results, and Playwright test results.

* [`docs/VISUAL_EVIDENCE.md`](docs/VISUAL_EVIDENCE.md)
  Provides screenshots showing the Docker runtime stack, GitHub commit activity, repository structure, Grafana dashboard, and Prometheus target health.

* [`reports/release_readiness_report.txt`](reports/release_readiness_report.txt)
  Shows an example release readiness report with pass/fail evidence, risk level, release status, and recommendation.

* [`docs/adr/`](docs/adr/)
  Contains Architecture Decision Records explaining key engineering decisions behind the framework design.


## Example Release Report

```text
==========================================================
SDET RELIABILITY FRAMEWORK - RELEASE READINESS REPORT
==========================================================

Docker Build                        PASS
Python Tests                        PASS
Playwright Observability Tests      PASS
API Health                          PASS
Metrics Endpoint                    PASS
Prometheus API                      PASS

----------------------------------------------------------

Total Checks  : 9
Failed Checks : 0
Risk Level    : LOW
Overall Status: READY FOR RELEASE
Recommendation: Proceed with release.
```

---

## Repository Structure

```text
.
├── api_service/          FastAPI application
├── docs/                 Architecture and engineering documentation
├── reports/              Generated reports and evidence
├── scripts/              Release assessment and automation utilities
├── tests/
│   ├── api/              API validation tests
│   ├── baselines/        Baseline and reporting tests
│   ├── fhir/             FHIR validation and workflow tests
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

## Engineering Documentation

Major architectural decisions are documented separately.

See:

* [`docs/SYSTEM_ARCHITECTURE.md`](docs/SYSTEM_ARCHITECTURE.md)
* [`docs/ENGINEERING_DECISIONS.md`](docs/ENGINEERING_DECISIONS.md)
* [`docs/LOCAL_VALIDATION_EVIDENCE.md`](docs/LOCAL_VALIDATION_EVIDENCE.md)

These documents explain:

* Architectural rationale
* Design tradeoffs
* Framework evolution
* Local validation evidence
* Future direction

---

## Running the Framework Locally

### 1. Clone the Repository

```bash
git clone <repository-url>
cd sdet-reliability-framework
```

---

### 2. Create a Python Virtual Environment

```bash
python -m venv .venv
```

Activate on Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, use the virtual environment Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

---

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

Or, using Python module syntax:

```powershell
python -m pip install -r requirements.txt
```

---

### 4. Install Playwright Dependencies

```bash
npm install
npx playwright install
```

---

### 5. Start the Docker Stack

```bash
docker compose up --build
```

Or run in detached mode:

```bash
docker compose up --build -d
```

---

### 6. Confirm Containers Are Running

```powershell
docker ps
```

Expected services include:

* `sdet-reliability-api`
* `sdet-prometheus`
* `sdet-grafana`

---

### 7. Validate API Health

```powershell
Invoke-RestMethod http://localhost:8000/health
```

Expected result:

```text
status: UP
```

---

### 8. Validate Metrics Export

```powershell
Invoke-RestMethod http://localhost:8000/metrics
```

Expected result:

```text
Prometheus-compatible metrics output
```

---

### 9. Validate Prometheus

```powershell
Invoke-RestMethod http://localhost:9090/-/healthy
```

Expected result:

```text
Prometheus Server is Healthy.
```

Prometheus targets can be reviewed at:

```text
http://localhost:9090/targets
```

---

### 10. Open Grafana

```text
http://localhost:3000
```

Default local credentials may be:

```text
admin / admin
```

---

## Running Tests

### Run Python Tests

```powershell
python -m pytest -q
```

Expected result:

```text
All Python tests pass
```

---

### Run Playwright Tests

```powershell
npx playwright test
```

Expected result:

```text
All Playwright tests pass
```

---

### Open the Playwright HTML Report

```powershell
npx playwright show-report
```

---

## Local Validation Workflow

A typical local validation workflow is:

```powershell
docker ps
Invoke-RestMethod http://localhost:8000/health
Invoke-RestMethod http://localhost:8000/metrics
Invoke-RestMethod http://localhost:9090/-/healthy
python -m pytest -q
npx playwright test
```

This validates:

* Container health
* API availability
* Metrics export
* Prometheus health
* Python automated tests
* Playwright automated tests

---

## Current Status

The framework currently demonstrates:

* Running FastAPI service
* Dockerized local reliability stack
* Prometheus metrics export
* Grafana dashboard support
* Python automated test coverage
* Playwright automated test coverage
* Security workflow validation
* Synthetic canary checks
* Mocked failure simulation
* Network inspection
* Performance baseline and trend reporting
* Release readiness reporting
* Local validation evidence documentation

---

## Career Relevance

This project demonstrates practical Quality Engineering and reliability-focused testing skills relevant to roles such as:

* QA Engineer
* SDET
* QA Automation Engineer
* Application Support Engineer
* Reliability Engineer
* Performance Test Engineer
* Healthcare IT Quality Analyst
* Production Support Engineer

The project emphasizes deterministic validation, reproducible test evidence, observability, and release decision support.

---

## Future Enhancements

Potential future improvements include:

* Additional QualitySignal providers
* Expanded Grafana dashboard examples
* CI/CD release gate enforcement
* Automated release report generation in GitHub Actions
* Additional synthetic journey coverage
* Broader API contract validation
* More advanced performance regression thresholds
* Additional observability metrics
* Screenshot-based evidence capture
* Improved dashboard documentation

---

## Summary

The **SDET Reliability Framework** demonstrates how automated testing, observability, health validation, performance signals, and release assessment can work together as a practical Quality Engineering system.

The goal is not only to test whether features work, but to produce evidence that supports reliable release decisions.

Overall focus:

```text
Test → Observe → Validate → Assess Risk → Recommend
```
