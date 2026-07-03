# CI Pipeline Overview

## Purpose

This document explains the GitHub Actions CI pipeline used by the SDET Reliability Framework.

The pipeline is designed to demonstrate automated validation across build, backend reliability, API testing, automation testing, observability, and release-readiness results.

The goal is not only to run tests, but to show how validation results can support a release decision.

## Pipeline Trigger

The CI pipeline runs automatically on:

- pushes to the `main` branch
- pull requests targeting the `main` branch

This supports continuous validation whenever code changes are introduced.

## CI Jobs

The workflow contains three main validation jobs:

1. Docker build validation
2. Python reliability and security tests
3. Playwright and Postman/Newman automation tests

---

## 1. Docker Build Validation

The Docker build validation job runs on Ubuntu.

It performs the following steps:

- checks out the repository
- builds the FastAPI Docker image
- verifies that the Docker image was created successfully

### Why This Matters

This confirms that the backend service can be packaged into a containerized image.

Container validation is important because modern QA and reliability workflows often depend on repeatable environments rather than manual local setup.

---

## 2. Python Reliability and Security Tests

The Python test job runs on Windows.

It performs the following steps:

- checks out the repository
- installs Python 3.11
- installs project dependencies
- starts the FastAPI service with Uvicorn
- runs the Python/Pytest validation suite
- runs the performance CI gate

### Why This Matters

This job validates backend behavior and reliability checks using Python-based automated tests.

The performance CI gate reinforces the idea that release readiness should consider more than simple pass/fail functional testing.

---

## 3. Playwright and Postman/Newman Automation Tests

The Playwright automation job runs on Ubuntu.

It performs the following steps:

- checks out the repository
- starts the Docker Compose observability stack
- waits for the FastAPI `/health` endpoint to become available
- installs Node.js dependencies
- runs Postman/Newman REST API validation
- generates a Newman XML report
- uploads the Newman report as a GitHub Actions artifact
- installs Playwright browsers
- runs the focused Playwright automation suite
- shuts down the Docker Compose stack

### Why This Matters

This job validates the system through multiple modern testing layers:

- REST API validation with Postman/Newman
- backend health validation
- metrics endpoint validation
- OpenAPI contract validation
- negative endpoint behavior
- Playwright automation
- observability stack validation
- downloadable test results

This demonstrates that API and automation tests can be run as part of a repeatable CI quality gate.

---

## Postman/Newman CI Artifact

The pipeline uploads the Newman XML report as a GitHub Actions artifact.

Artifact name:

```text
postman-newman-results

