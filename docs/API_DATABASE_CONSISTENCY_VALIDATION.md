# API-to-Database Consistency Validation

## Purpose

This validation checks that the patient lookup API response matches the direct PostgreSQL query result.

The goal is to verify consistency between the API layer and the database layer when the application is running in PostgreSQL-backed mode.

## Validation Flow

The validation script performs the following checks:

1. Confirms the PostgreSQL container is running.
2. Confirms the API container is running.
3. Confirms the API is configured with `PATIENT_DATA_SOURCE=postgres`.
4. Confirms the API health endpoint returns `UP`.
5. Calls the patient lookup API.
6. Queries PostgreSQL directly for the same patient.
7. Compares the API response fields to the database result fields.
8. Confirms missing patient behavior remains consistent.

## Script

Run:

    powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\validate_api_database_consistency.ps1

## Compared Fields

The script compares:

- patient_id
- name
- status
- last_visit

## Validated Patient Cases

| Patient ID | Scenario |
|---|---|
| 1001 | Active patient with completed encounters |
| 1002 | Inactive patient with completed encounter |
| 1003 | Active patient with no completed encounters |
| 1004 | Active patient with completed and scheduled encounters |
| 9999 | Missing patient returns API 404 and no database row |

## Business Rule Covered

The validation confirms that `last_visit` is calculated from completed encounters only.

This matters for patient 1004 because the database contains both a completed encounter and a scheduled encounter. The API response should use the latest completed encounter date, not the scheduled encounter date.

## Scope

This validation is read-only.

It does not insert, update, delete, migrate, or modify database records.

## Data Safety

All data is synthetic. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.
