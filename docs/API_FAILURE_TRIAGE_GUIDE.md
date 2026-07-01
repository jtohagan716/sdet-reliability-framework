# API Failure Triage Guide

## Purpose

This guide explains how to diagnose REST API validation failures in the SDET Reliability Framework.

The goal is to provide a structured troubleshooting workflow for failures involving:

- FastAPI startup
- Docker container health
- REST API endpoint behavior
- Pytest API tests
- Postman/Newman API tests
- OpenAPI contract checks
- GitHub Actions CI failures
- release-readiness evidence

This guide reflects a production-support mindset: start with the symptom, collect evidence, isolate the failure layer, identify the root cause, fix the issue, and revalidate.

---

## Triage Mindset

When an API test fails, do not guess.

Use this sequence:

1. Confirm the service is running.
2. Confirm the expected container is healthy.
3. Check the known-good `/health` endpoint.
4. Reproduce the failing endpoint manually.
5. Review logs.
6. Determine whether the issue is application code, test code, environment, data, or CI setup.
7. Fix one thing at a time.
8. Re-run focused validation.
9. Re-run broader regression validation.
10. Preserve useful evidence.

The goal is not only to fix the failure. The goal is to understand what the failure proves.

---

## Quick Triage Flow

```text
API test failed
   |
   v
Is the API container running?
   |
   +-- No --> docker ps -a --> docker logs sdet-reliability-api
   |
   +-- Yes
        |
        v
Does /health respond?
        |
        +-- No --> service readiness / startup / port issue
        |
        +-- Yes
             |
             v
Can the failing endpoint be reproduced manually?
             |
             +-- No --> test/environment mismatch
             |
             +-- Yes
                  |
                  v
Is the actual response different from expected?
                  |
                  +-- Yes --> API behavior or test expectation issue
                  |
                  +-- No --> automation layer issue

Core Diagnostic Commands
Check Git State

Before debugging, confirm the working tree.

git status
git branch --show-current

Why this matters:

If the working tree is dirty or the wrong branch is active, you may be testing code that is not what you think it is.

Start or Rebuild the Docker Stack
docker compose up -d --build

Use this after changing backend code.

Stop the Docker Stack
docker compose down

Use this when you need a clean restart.

Check Running Containers
docker ps

Expected containers:

sdet-reliability-api
sdet-prometheus
sdet-grafana

The API container should show port 8000 mapped:

0.0.0.0:8000->8000/tcp

Ideally it should also show:

healthy
Check All Containers, Including Failed Ones
docker ps -a

Use this when the API is not reachable and the API container is missing from docker ps.

A missing API container often means:

the container started and exited
the application failed during startup
there is a Python import, syntax, or runtime error
Review API Container Logs
docker logs sdet-reliability-api

This is one of the most important commands.

Look for errors such as:

NameError
ImportError
SyntaxError
IndentationError
ModuleNotFoundError
Application startup failed
Known Failure Example: Missing FastAPI Import

During implementation of the synthetic patient API endpoint, the API container initially failed to stay running.

The symptom was:

Invoke-RestMethod : Unable to connect to the remote server

The container check showed that the API container was missing:

docker ps

Prometheus and Grafana were running, but sdet-reliability-api was not.

The logs showed:

NameError: name 'Path' is not defined

Root cause:

The endpoint used FastAPI's Path helper, but Path was not imported.

A second error appeared after fixing that:

NameError: name 'Header' is not defined

Root cause:

The existing Header import had been accidentally removed while updating the FastAPI import line.

Final corrected import:

from fastapi import FastAPI, Header, HTTPException, Path

Triage lesson:

A container can appear to start during docker compose up, but still exit immediately if the application fails during startup. Always confirm with docker ps and docker logs.

Health Endpoint Triage

The /health endpoint is the first endpoint to check.

Invoke-RestMethod http://localhost:8000/health

Expected result:

status: UP

If /health fails, do not start debugging deeper endpoints yet.

First check:

docker ps
docker ps -a
docker logs sdet-reliability-api

Possible causes:

Symptom	Possible Cause
Cannot connect to localhost:8000	API container not running or port not exposed
API container missing	Application crashed during startup
API container restarting	Startup error or health check failure
/health returns non-200	application-level health issue
Slow response	service readiness or local resource issue
Synthetic Patient Endpoint Triage

The synthetic patient endpoint is:

GET /patients/{patient_id}

Expected behavior:

Request	Expected Status
GET /patients/1001	200
GET /patients/1002	200
GET /patients/9999	404
GET /patients/abc	422
POST /patients/1001	405
Valid Patient Should Return 200

Command:

Invoke-RestMethod http://localhost:8000/patients/1001

Expected result:

{
  "patient_id": 1001,
  "name": "Alex Morgan",
  "status": "active",
  "last_visit": "2026-06-15"
}

If this fails:

confirm /health works
confirm the API container is running
check whether the endpoint exists in api_service/app.py
check logs
check whether Docker was rebuilt after code changes
Unknown Patient Should Return 404

Command:

try {
    Invoke-RestMethod http://localhost:8000/patients/9999
} catch {
    $_.Exception.Response.StatusCode.value__
}

Expected result:

404

If this returns 200, the API may be incorrectly returning data for unknown IDs.

If this returns 500, the API may not be handling missing data safely.

A controlled 404 is the correct behavior for a missing resource.

Invalid Patient ID Should Return 422

Command:

try {
    Invoke-RestMethod http://localhost:8000/patients/abc
} catch {
    $_.Exception.Response.StatusCode.value__
}

Expected result:

422

Why this happens:

The route expects:

patient_id: int

So FastAPI rejects abc before the endpoint logic runs.

A 422 response indicates path-parameter validation is working.

Unsupported Method Should Return 405

Command:

try {
    Invoke-RestMethod -Method Post http://localhost:8000/patients/1001
} catch {
    $_.Exception.Response.StatusCode.value__
}

Expected result:

405

Why this matters:

The API supports:

GET /patients/{patient_id}

It does not support:

POST /patients/{patient_id}

A controlled 405 Method Not Allowed confirms the method boundary is clear.

OpenAPI Contract Triage

The OpenAPI contract should document the patient endpoint.

Command:

$openapi = Invoke-RestMethod http://localhost:8000/openapi.json
$openapi.paths.PSObject.Properties.Name

Expected path:

/patients/{patient_id}

If the endpoint works but does not appear in OpenAPI:

confirm the route is registered with FastAPI
confirm the app was rebuilt and restarted
confirm you are testing the correct container/image
check whether the route is conditionally loaded
review api_service/app.py

Contract visibility matters because API consumers, testers, and automation tools often rely on OpenAPI documentation.

Pytest API Failure Triage

Run the synthetic patient API tests:

python -m pytest tests\test_synthetic_patient_api.py -q

Expected:

7 passed

If a test fails, re-run with more detail:

python -m pytest tests\test_synthetic_patient_api.py -vv

Common Pytest failure categories:

Failure Type	What It Usually Means
Expected 200, got 404	test data missing or endpoint lookup changed
Expected 404, got 200	API is returning data for unknown resource
Expected 422, got another status	path parameter type validation changed
Expected field missing	response model or response body changed
Sensitive field present	unsafe response data added
OpenAPI path missing	route not documented or not registered

Triage sequence:

Read the failed assertion.
Identify expected vs. actual value.
Reproduce manually if useful.
Check whether the API behavior changed intentionally.
If behavior changed intentionally, update tests and documentation.
If behavior changed unintentionally, fix the API.
Re-run the focused test.
Re-run the full Pytest suite.
Postman/Newman Failure Triage

Run the Postman/Newman API suite:

npm run postman:test

Expected:

requests: 10 executed, 0 failed
test-scripts: 10 executed, 0 failed
assertions: 37 executed, 0 failed

If Newman fails, look for:

failing request name
failed assertion text
actual status code
response body
response-time threshold failure
environment variable issues

Common Newman failure categories:

Failure Type	Possible Cause
Cannot connect	API not running or wrong base_url
Expected 200, got 404	endpoint missing or wrong path
Expected 404, got 200	negative behavior changed
JSON assertion failed	response body changed
response time exceeded threshold	local slowness or performance regression
OpenAPI path missing	contract no longer documents endpoint
environment variable missing	Postman environment not loaded
Postman Environment Triage

The Postman environment should define:

base_url = http://localhost:8000
max_response_ms = 1000

If Newman cannot reach the API, check:

postman/SDET_Reliability_Local.postman_environment.json

Then confirm the Newman command uses the environment:

npm run postman:test

The script should run Newman with:

-e postman/SDET_Reliability_Local.postman_environment.json
Newman XML Report Triage

Generate the XML report:

npm run postman:test:report

Expected report path:

reports/postman-newman-results.xml

If the report is missing:

confirm the reports folder exists
confirm the npm script includes the JUnit reporter
confirm Newman completed successfully
check the command output for reporter errors

The XML report is useful because it provides machine-readable test evidence for CI and release review.

GitHub Actions CI Failure Triage

If a pull request or push fails in GitHub Actions, inspect the failed job.

Current CI areas include:

Docker build validation
Python reliability tests
performance gate execution
Postman/Newman API validation
Newman XML artifact upload
Playwright automation tests
Docker Compose observability stack validation

Triage steps:

Open the failed GitHub Actions run.
Identify the failed job.
Identify the failed step.
Expand the log output.
Determine whether the failure is build, service startup, Pytest, Newman, Playwright, or artifact upload.
Reproduce locally when possible.
Fix the smallest responsible issue.
Push the fix and let CI re-run.
CI Failure Categories
Failed Area	Likely Cause	First Place to Look
Docker build	Dockerfile or dependency issue	Docker build logs
Service readiness	API failed to start or health check failed	Docker logs
Pytest	code behavior changed or test expectation wrong	Pytest failure output
Performance gate	threshold exceeded	performance gate output
Newman	API assertion failed or service unavailable	Newman output
Artifact upload	report missing or wrong path	artifact upload step
Playwright	app behavior, browser dependency, or timing issue	Playwright logs
Release-Readiness Interpretation

Not all failures carry the same risk.

Failure	Release Impact
/health fails	Block release
valid patient endpoint returns wrong data	Block affected release
unknown patient does not return 404	Investigate before release
invalid ID does not return 422	Investigate validation behavior
sensitive field appears in response	Block release
OpenAPI path missing	Investigate contract risk
Newman XML report missing	Investigate evidence/reporting gap
CI fails	Do not merge until understood

The key principle:

A failing test is not just a red mark. It is evidence of a risk that needs interpretation.

Evidence to Capture

When documenting an API failure, capture:

branch name
commit hash
command run
endpoint tested
expected result
actual result
status code
response body
relevant logs
failed CI job or step
fix applied
validation after fix

This supports reproducibility and helps developers, testers, and reviewers understand the issue.

Example Failure Report Format
Issue:
GET /patients/9999 returned unexpected behavior.

Expected:
404 Not Found with controlled error detail.

Actual:
500 Internal Server Error.

Environment:
Local Docker Compose stack.

Evidence:
- docker ps showed API container healthy
- manual endpoint call reproduced issue
- Pytest negative test failed
- logs showed unhandled missing-key lookup

Root Cause:
Endpoint attempted to access missing synthetic patient data without controlled error handling.

Fix:
Added HTTPException(status_code=404) for unknown synthetic patient IDs.

Validation:
- GET /patients/9999 returned 404
- Pytest focused test passed
- full Pytest suite passed
- Newman API suite passed