# Diagnostic Logging and Request Timing

## Purpose

This project uses diagnostic logging to make API behavior easier to troubleshoot during local validation, CI investigation, and release-readiness review.

The goal is not just to confirm that an endpoint returned a response. The goal is to capture enough safe operational evidence to understand what happened during a request.

## Agile Testing Context

This work supports the following reliability story:

As a reliability-focused QA/SDET, I want the API to log request handling and timing, so that failures and slow behavior can be diagnosed with evidence.

## Acceptance Criteria

- The API supports configurable `LOG_LEVEL`.
- Each request logs when it starts.
- Each request logs when it completes.
- Completion logs include method, path, status code, and duration in milliseconds.
- Patient lookup success is logged safely.
- Patient lookup not-found behavior is logged safely.
- Logs do not expose PHI, PII, secrets, tokens, credentials, or full patient records.
- Existing Pytest, Newman, and local smoke validation checks continue to pass.

## Configuration

The API reads the logging level from the `LOG_LEVEL` environment variable.

Default:

```text
LOG_LEVEL=INFO
Supported values follow standard Python logging levels, such as:

DEBUG
INFO
WARNING
ERROR
Request Timing Logs

The API logs request start and request completion through FastAPI middleware.

Example successful request:

request_start method=GET path=/patients/1001
request_complete method=GET path=/patients/1001 status_code=200 duration_ms=51.17

This helps confirm:

which endpoint was called
whether the request completed
which HTTP status code was returned
how long the request took
Patient Lookup Logs

The synthetic patient endpoint logs lookup decisions without logging full patient records.

Example successful lookup:

patient_lookup_started patient_id=1001
patient_lookup_success patient_id=1001 status=active

Example missing patient lookup:

patient_lookup_started patient_id=9999
patient_lookup_not_found patient_id=9999
Safe Logging Policy

The application may log:

request method
request path
status code
duration in milliseconds
synthetic patient ID
lookup result
non-sensitive synthetic status values

The application must not log:

real patient information
PHI
PII
credentials
secrets
tokens
passwords
full patient records
Troubleshooting Workflow

When an API check fails:

Confirm the Docker containers are running.
Reproduce the request manually.
Review the API logs.
Look for request_start.
Look for endpoint-specific diagnostic logs.
Look for request_complete.
Confirm the status code and duration_ms.
Compare the observed behavior to Pytest, Newman, and smoke validation expectations.
Release-Readiness Value

Diagnostic logging supports release-readiness by providing evidence that the API can be observed during normal, negative, and failure-path validation.

This improves the ability to identify whether a failure is caused by:

application logic
invalid input
missing test data
runtime/container issues
slow response behavior
test or environment configuration

