# API Contract Validation

## Summary

This document describes the API contract validation added to the SDET Reliability Framework.

API contract validation checks that an Application Programming Interface (API) response keeps the structure and data types that consumers expect. This is different from only checking that an endpoint returns a successful status code.

A response can return the expected status code while still breaking consumers if field names, required fields, data types, or error formats change unexpectedly.

## Purpose

The purpose of this validation layer is to confirm that core API responses remain stable.

The validation checks:

- response status codes
- JSON response structure
- required fields
- expected data types
- date and datetime formatting
- expected success response shape
- expected error response shape

## Validated Endpoints

| Endpoint | Expected Result |
|---|---|
| /health | Health response contract |
| /patients/1001 | Successful patient response contract |
| /patients/1002 | Successful patient response contract |
| /patients/9999 | Missing patient error contract |
| /patients/abc | Invalid patient identifier error contract |

## Patient Response Contract

Successful patient lookup responses are expected to return a JSON object with the following fields:

| Field | Expected Type | Notes |
|---|---|---|
| patient_id | integer | Synthetic patient identifier |
| name | string | Non-empty synthetic patient name |
| status | string | Expected patient status |
| last_visit | string | ISO date format, YYYY-MM-DD |

Allowed patient status values:

- active
- inactive

## Health Response Contract

The health endpoint is expected to return a JSON object with the following fields:

| Field | Expected Type | Notes |
|---|---|---|
| status | string | Expected value is UP |
| timestamp_utc | string | ISO datetime format |

## Error Response Contracts

Error responses are also part of the API contract.

### Missing Patient

A missing patient lookup is expected to return:

| Item | Expected Value |
|---|---|
| Status code | 404 |
| Body format | JSON object |
| Required field | detail |
| detail type | string |

### Invalid Patient Identifier

An invalid patient identifier is expected to return:

| Item | Expected Value |
|---|---|
| Status code | 422 |
| Body format | JSON object |
| Required field | detail |
| detail type | list |

The validation also checks that the first validation error includes:

- loc
- msg
- type

## Test File

The API contract validation tests are located at:

    tests/test_api_contract_validation.py

Run only the contract validation tests with:

    python -m pytest .\tests\test_api_contract_validation.py -v

Run the full backend test suite with:

    python -m pytest

## Why This Matters

API contract validation helps detect breaking response changes early.

Examples of breaking contract changes include:

- renaming patient_id to id
- removing last_visit
- changing patient_id from an integer to a string
- changing the error response format
- returning a date in an unexpected format

These changes may not always be caught by basic status-code checks.

## Current Scope

This validation is focused on the current synthetic API endpoints.

It does not replace full OpenAPI schema validation or consumer-driven contract testing. Those could be added in future milestones.
