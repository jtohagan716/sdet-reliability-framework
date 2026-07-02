# Request ID Traceability

## Purpose

This project uses request IDs to make individual API requests traceable across application logs.

Diagnostic logging tells us what happened. Request ID traceability helps us connect multiple log lines to the same request.

## Agile Testing Context

This work supports the following reliability story:

As a reliability-focused QA/SDET, I want every API request to have a request ID, so that one request can be traced across logs during troubleshooting.

## Acceptance Criteria

- The API accepts an incoming `X-Request-ID` header.
- The API generates a request ID when one is not provided.
- The API returns `X-Request-ID` in the response headers.
- Request start logs include `request_id`.
- Request completion logs include `request_id`.
- Synthetic patient lookup logs include `request_id`.
- Existing API behavior remains unchanged.
- Pytest, Newman, and local smoke validation checks continue to pass.

## Behavior

If a caller provides an `X-Request-ID` header, the API uses that value.

Example:

    X-Request-ID: james-test-request-id-123

If a caller does not provide an `X-Request-ID`, the API generates one automatically.

The response includes the request ID in the response headers:

    X-Request-ID: <request-id>

## Example Trace

A successful patient lookup can now be traced across multiple log lines:

    request_start request_id=james-test-request-id-123 method=GET path=/patients/1001
    patient_lookup_started request_id=james-test-request-id-123 patient_id=1001
    patient_lookup_success request_id=james-test-request-id-123 patient_id=1001 status=active
    request_complete request_id=james-test-request-id-123 method=GET path=/patients/1001 status_code=200 duration_ms=12.4

A missing patient lookup can also be traced:

    request_start request_id=missing-patient-test-9999 method=GET path=/patients/9999
    patient_lookup_started request_id=missing-patient-test-9999 patient_id=9999
    patient_lookup_not_found request_id=missing-patient-test-9999 patient_id=9999
    request_complete request_id=missing-patient-test-9999 method=GET path=/patients/9999 status_code=404 duration_ms=8.2

## Safe Logging Policy

Request IDs should help troubleshoot behavior without exposing sensitive data.

The application may log:

- request ID
- request method
- request path
- status code
- duration in milliseconds
- synthetic patient ID
- lookup result

The application must not log:

- PHI
- PII
- secrets
- credentials
- passwords
- tokens
- full patient records

## Testing Coverage

Pytest validates that:

- `X-Request-ID` is generated when missing.
- Caller-provided `X-Request-ID` values are preserved.
- Existing synthetic patient API behavior remains stable.

The local smoke validation confirms that the Docker runtime, API health check, synthetic patient API, Pytest checks, and Newman API regression continue to pass.

## Reliability Value

Request ID traceability improves troubleshooting by letting a tester or support engineer follow one request across logs from start to finish.

This is especially useful when investigating:

- intermittent failures
- unexpected status codes
- slow requests
- missing test data
- API behavior across multiple validation tools
- CI or smoke-test failures