# v1.4.0 - PostgreSQL Schema and Seed Data

## Summary

This milestone introduces the PostgreSQL database foundation for the reliability validation project.

The database uses synthetic healthcare-style data and is intended to support future API/database consistency checks, SQL validation, query plan review, and database-backed performance testing.

## Added

- PostgreSQL schema SQL file
- Synthetic seed data SQL file
- SQL practice query file
- Normalized relational tables
- Primary keys and foreign keys
- Basic check constraints
- Many-to-many relationship between encounters and diagnoses

## Tables

- patients
- facilities
- providers
- encounters
- diagnoses
- encounter_diagnoses
- lab_orders
- lab_results

## Validation Purpose

This database foundation supports future validation of:

- API responses against database state
- relational integrity
- join behavior
- left join and anti-join patterns
- many-to-many relationships
- aggregation queries
- Common Table Expressions
- window functions
- query plan and index performance comparisons

## Data Safety

All data is synthetic. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## Current Scope

This milestone adds the database schema and seed data foundation. API routes are not yet required to read from PostgreSQL in this milestone.

## Future Improvements

- Add PostgreSQL service to Docker Compose
- Add automated database initialization validation
- Add API/database consistency tests
- Add database-backed patient lookup
- Add EXPLAIN ANALYZE query plan comparison
- Add index performance comparison

## Docker Compose Validation

PostgreSQL was added as a Docker Compose service using the official postgres:16 image.

The service initializes the synthetic reliability database from SQL files mounted into:

/docker-entrypoint-initdb.d

Validated locally:

- PostgreSQL container started successfully.
- Database accepted connections.
- Schema initialization completed.
- Eight relational tables were created.
- Synthetic seed data loaded successfully.

Validated tables:

- patients
- facilities
- providers
- encounters
- diagnoses
- encounter_diagnoses
- lab_orders
- lab_results

## Important Initialization Note

PostgreSQL initialization scripts in docker-entrypoint-initdb.d run only when the database volume is first created.

If schema or seed files are changed later during local development, the local PostgreSQL volume may need to be recreated with:

docker compose down -v
docker compose up -d postgres

This is destructive for the local database volume and should only be used for this project-scale synthetic database environment.
