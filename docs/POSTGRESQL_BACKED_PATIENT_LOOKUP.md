# PostgreSQL-Backed Patient Lookup

## Purpose

This milestone connects the synthetic patient lookup API to PostgreSQL when the application is running through Docker Compose.

The goal is to preserve the existing external API contract while changing the internal data source from in-memory synthetic data to PostgreSQL-backed synthetic data.

## Data Source Behavior

The patient lookup endpoint supports two data source modes:

| Mode | Description |
|---|---|
| memory | Uses the in-memory synthetic patient dictionary |
| postgres | Uses PostgreSQL through a parameterized SQL query |

The default mode is:

    memory

Docker Compose sets:

    PATIENT_DATA_SOURCE=postgres

and provides:

    DATABASE_URL=postgresql://sdet_user:sdet_password@postgres:5432/sdet_reliability

## Endpoint

The database-backed behavior applies to:

    GET /patients/{patient_id}

## Expected Responses

Synthetic patient 1001:

    patient_id: 1001
    name: Alex Morgan
    status: active
    last_visit: 2026-06-15

Synthetic patient 1002:

    patient_id: 1002
    name: Jordan Lee
    status: inactive
    last_visit: 2026-05-20

Missing synthetic patient 9999:

    404 Not Found

Invalid non-integer patient IDs continue to return FastAPI validation errors.

## SQL Query Pattern

The PostgreSQL-backed lookup uses direct parameterized SQL.

The query joins patients to completed encounters to calculate the latest completed visit date.

The query demonstrates:

- parameterized SQL
- left join behavior
- filtering completed encounters
- aggregation with MAX
- grouping
- API response shaping from database results

## Validation Script

Run the PostgreSQL-backed API validation with:

    .\scripts\validate_postgresql_patient_lookup.ps1

The script validates:

- PostgreSQL container is running
- API container is running
- API container is configured for PostgreSQL mode
- `/health` returns UP
- `/patients/1001` returns the expected PostgreSQL-backed response
- `/patients/1002` returns the expected PostgreSQL-backed response
- `/patients/9999` returns 404
- API logs include the PostgreSQL data source marker

## Scope

This milestone validates read-only patient lookup behavior.

It does not add patient inserts, updates, deletes, migrations, authentication changes, or production database behavior.

## Data Safety

All data is synthetic. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.
