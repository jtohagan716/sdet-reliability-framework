@'
# Postman API Testing

## Purpose

This project includes a Postman API testing layer to demonstrate REST API and backend service validation for the SDET Reliability Framework.

The Postman collection validates backend health, observability endpoints, OpenAPI contract availability, expected response fields, HTTP status codes, response-time thresholds, and controlled negative API behavior.

This adds a recognizable API testing toolset alongside the existing Python, Playwright, Docker, Prometheus, Grafana, GitHub Actions, and release-readiness validation work.
## Related API Testing Documents

This document explains the Postman/Newman implementation.

Additional API testing artifacts:

- [REST API Testing Strategy](REST_API_TESTING_STRATEGY.md) — explains the broader API testing approach, including positive testing, negative testing, contract awareness, response validation, CI execution, and release-readiness value.
- [API Test Case Matrix](API_TEST_CASE_MATRIX.md) — maps specific API endpoints and scenarios to expected status codes, validation points, automation layers, and release impact.

## Files

| File | Purpose |
|---|---|
| `postman/SDET_Reliability_Framework.postman_collection.json` | Postman collection containing API requests and test assertions |
| `postman/SDET_Reliability_Local.postman_environment.json` | Local Postman environment using `http://localhost:8000` as the backend base URL |
| `reports/postman-newman-results.xml` | Newman-generated JUnit-style XML report from command-line execution |

## API Coverage

| Request | Validation |
|---|---|
| `GET /health` | Confirms the backend service is reachable and reports `UP` status |
| `GET /metrics` | Confirms Prometheus-compatible metrics are exposed for observability |
| `GET /openapi.json` | Confirms the FastAPI OpenAPI contract is available |
| `GET /invalid-endpoint` | Confirms invalid routes return controlled `404` responses |

## Validation Types Demonstrated

The Postman collection demonstrates:

- REST API status-code validation
- JSON response-field validation
- response-time threshold checks
- OpenAPI contract availability checks
- observability endpoint validation
- negative API testing
- repeatable local API test execution
- command-line API test execution with Newman
- machine-readable test reporting through JUnit-style XML output

## Running Manually in Postman

Start the local Docker stack:

```powershell
docker compose up -d
```

Import the Postman collection:

```text
postman/SDET_Reliability_Framework.postman_collection.json
```

Import the Postman environment:

```text
postman/SDET_Reliability_Local.postman_environment.json
```

Select the environment:

```text
SDET Reliability Local
```

Run the collection with Postman Collection Runner.

## Running from the Command Line

Install dependencies:

```powershell
npm install
```

Run the Postman collection with Newman:

```powershell
npm run postman:test
```

Run the collection and generate a JUnit-style XML report:

```powershell
npm run postman:test:report
```

The report is written to:

```text
reports/postman-newman-results.xml
```

## Example Validation Result

A successful Newman run should show:

```text
requests: 4 executed, 0 failed
test-scripts: 4 executed, 0 failed
assertions: 11 executed, 0 failed
```

This confirms that the backend API endpoints were reachable and that all Postman assertions passed.

## What This Adds to the Framework

This Postman layer validates that the backend REST API is:

- reachable
- healthy
- observable
- contract-visible through OpenAPI
- returning expected response fields
- returning expected HTTP status codes
- handling invalid routes in a controlled way
- capable of producing repeatable test results

## Release-Readiness Value

Postman API testing adds another validation layer to the framework by confirming that backend REST endpoints are reachable, contract-visible, observable, and returning controlled responses.

This supports release-readiness decisions by adding clear REST API results alongside Python tests, Playwright automation, Docker validation, Prometheus metrics, Grafana observability, GitHub Actions CI, and release reporting.

### CI-Integrated Postman/Newman API Validation

The framework runs Postman/Newman REST API validation in GitHub Actions as part of the automated CI workflow.

The CI pipeline:

- starts the Docker Compose reliability stack
- waits for the FastAPI service health check to pass
- runs the Postman collection with Newman
- generates a JUnit-style XML report
- uploads the Newman report as a GitHub Actions artifact
- continues into the Playwright automation suite

This demonstrates repeatable backend API validation, CI-based quality gates, and downloadable test results.

## Professional Relevance

This work demonstrates practical exposure to REST API testing and backend service validation using Postman and Newman.

It supports job requirements such as:

- experience testing REST APIs
- backend service validation
- API response assertion testing
- status-code validation
- negative API testing
- OpenAPI contract awareness
- repeatable automated test execution
- CI/CD-style test reporting



