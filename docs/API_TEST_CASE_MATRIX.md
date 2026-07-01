# API Test Case Matrix

## Purpose

This document defines the REST API test case matrix for the SDET Reliability Framework.

The goal of this matrix is to show how API testing is planned, organized, and connected to release-readiness evidence. Rather than testing endpoints randomly, the matrix identifies the endpoint, method, scenario, expected behavior, validation points, automation layer, and release impact.

This helps demonstrate professional API test design across:

- positive API scenarios
- negative API scenarios
- status-code validation
- response-body validation
- OpenAPI contract awareness
- response-time threshold checks
- security-aware validation
- CI execution
- evidence generation
- release-readiness decision support

## Why an API Test Matrix Matters

A test matrix helps a QA engineer or SDET answer important questions before testing begins:

- What endpoints are in scope?
- What behavior should each endpoint demonstrate?
- What positive cases should pass?
- What negative cases should fail safely?
- What status codes are expected?
- What response fields should be validated?
- What security or sensitive-data concerns exist?
- Which tests are automated?
- Which tests run in CI?
- What evidence supports the result?
- Would a failure block release?

A professional API test effort should not only prove that endpoints return successful responses. It should also prove that invalid inputs, missing resources, unsupported behavior, and unsafe data exposure are handled correctly.

## API Test Design Principles

The SDET Reliability Framework uses the following principles for API test design:

1. **Validate behavior, not just availability**  
   A successful HTTP response is not enough. The response must include the expected structure, fields, and values.

2. **Test both positive and negative scenarios**  
   APIs should work correctly for valid requests and fail predictably for invalid requests.

3. **Check status codes intentionally**  
   Status codes should match the scenario being tested.

4. **Validate response bodies**  
   API tests should confirm important fields, values, and data structure.

5. **Use synthetic data only**  
   Test data must not include PHI, PII, real patient data, production logs, credentials, or secrets.

6. **Include contract awareness**  
   API schema and documented paths should be validated through OpenAPI where applicable.

7. **Include performance awareness**  
   Lightweight response-time thresholds can help identify obvious degradation.

8. **Preserve evidence**  
   Tests should produce output that can be reviewed locally or in CI.

9. **Connect test results to release readiness**  
   Test failures should be interpreted in terms of risk, not just pass/fail status.

## Current API Coverage

The framework currently validates core service, observability, and documentation endpoints.

| ID | Endpoint | Method | Scenario | Test Type | Expected Status | Validation Points | Automation Layer | Release Impact |
|---|---|---|---|---|---:|---|---|---|
| API-001 | `/health` | GET | Service health check succeeds | Positive / Availability | 200 | Response contains `status`; status is `UP`; response time under threshold | Postman/Newman, Pytest, CI health check | Failure may indicate service is unavailable or not ready for release |
| API-002 | `/metrics` | GET | Metrics endpoint is available | Positive / Observability | 200 | Body contains Prometheus-style output; includes `# HELP`; response has meaningful content | Postman/Newman, Playwright, Prometheus validation | Failure may indicate missing observability signal |
| API-003 | `/openapi.json` | GET | API contract is published | Positive / Contract | 200 | Response contains `openapi`, `info`, and `paths`; expected paths are documented | Postman/Newman | Failure may indicate missing or broken API contract visibility |
| API-004 | `/invalid-endpoint` | GET | Unknown endpoint fails safely | Negative / Error Handling | 404 | Response contains controlled error body; includes `detail` field | Postman/Newman | Failure may indicate unsafe or unclear API error behavior |

## Planned Synthetic Domain API Coverage

To deepen REST API testing, the project will add synthetic domain endpoints using fictional test data only.

The first planned endpoint is:

```text
GET /patients/{patient_id}