# API Contract Validation v1.2.0

## Summary

This release adds API contract validation to the SDET Reliability Framework.

The new validation checks confirm that selected Application Programming Interface (API) responses return the expected structure, required fields, data types, and error formats.

## Added

| Item | Description |
|---|---|
| Contract validation tests | Added Pytest checks for API response structure |
| Health response contract | Validates /health response fields and datetime format |
| Patient response contract | Validates synthetic patient response fields and data types |
| Missing patient error contract | Validates expected 404 error response shape |
| Invalid patient ID error contract | Validates expected 422 validation error shape |
| Documentation | Added API contract validation documentation |

## Test Coverage

The following endpoints are covered:

| Endpoint | Contract Validated |
|---|---|
| /health | status and timestamp_utc |
| /patients/1001 | patient_id, name, status, last_visit |
| /patients/1002 | patient_id, name, status, last_visit |
| /patients/9999 | 404 detail error format |
| /patients/abc | 422 validation error format |

## Validation Command

Run the contract validation tests with:

    python -m pytest .\tests\test_api_contract_validation.py -v

Run the full backend suite with:

    python -m pytest

## Current Scope

This release adds project-scale API contract validation.

It does not add a new application feature and does not replace full OpenAPI schema validation.
