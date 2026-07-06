# v1.6.0 - API-to-Database Consistency Validation

## Summary

This milestone adds API-to-database consistency validation for the PostgreSQL-backed patient lookup flow.

The validation compares API responses against direct PostgreSQL query results to confirm that the API layer and database layer remain aligned.

## Added

- API-to-database consistency validation script
- Direct SQL comparison against PostgreSQL
- Validation coverage for patients with completed encounters
- Validation coverage for a patient with no completed encounters
- Validation coverage for completed-versus-scheduled encounter behavior
- Missing patient consistency validation
- Documentation for API-to-database consistency validation

## Validation

Validated locally:

- PostgreSQL container is running
- API container is running
- API is configured with `PATIENT_DATA_SOURCE=postgres`
- API health endpoint returns `UP`
- Patient 1001 API response matches database result
- Patient 1002 API response matches database result
- Patient 1003 API response matches database result
- Patient 1004 API response matches database result
- Missing patient 9999 has no database row and returns API 404

## Business Rule

The validation confirms that `last_visit` is based only on completed encounters.

This is specifically validated through patient 1004, which has both completed and scheduled encounter data.

## Scope

This milestone adds read-only consistency validation.

It does not add write operations, migrations, authentication changes, or production database behavior.

## Data Safety

All data is synthetic. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## Future Improvements

- Add automated database consistency checks to the release quality gate
- Add query plan inspection for patient lookup SQL
- Add index comparison for patient lookup query performance
- Add database-backed performance baseline validation
