# v1.5.0 - PostgreSQL-Backed Patient Lookup

## Summary

This milestone connects the synthetic patient lookup API to PostgreSQL when running through Docker Compose.

The external API contract remains stable while the internal data source can now use PostgreSQL-backed synthetic data.

## Added

- PostgreSQL patient lookup repository
- database connection helper
- environment-based patient data source selection
- Docker Compose configuration for PostgreSQL-backed API mode
- PostgreSQL-backed patient lookup validation script
- PostgreSQL-backed patient lookup documentation

## Validation

Validated locally:

- PostgreSQL container is running
- API container is running
- API container uses `PATIENT_DATA_SOURCE=postgres`
- API health endpoint returns `UP`
- `/patients/1001` returns expected PostgreSQL-backed synthetic data
- `/patients/1002` returns expected PostgreSQL-backed synthetic data
- `/patients/9999` returns 404
- API logs include `data_source=postgres`
- Existing Python regression tests continue to pass
- PostgreSQL schema validation continues to pass

## API Contract

The patient summary response remains:

- patient_id
- name
- status
- last_visit

This milestone changes the internal data source, not the external response contract.

## SQL Behavior

The PostgreSQL lookup uses a parameterized SQL query that joins patients to completed encounters and calculates the latest completed encounter date with `MAX`.

The query supports continued SQL practice around:

- left joins
- filtering
- grouping
- aggregation
- parameterized database access

## Scope

This milestone adds read-only PostgreSQL-backed lookup behavior.

It does not add write operations, database migrations, authentication changes, or production database behavior.

## Data Safety

All data is synthetic. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## Future Improvements

- Add API-to-database consistency tests
- Add SQL join and data quality validation
- Add query plan inspection
- Add index performance comparison
- Add database-backed performance baseline checks
