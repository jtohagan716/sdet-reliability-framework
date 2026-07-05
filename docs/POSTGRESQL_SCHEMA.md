# PostgreSQL Schema

## Purpose

This project uses PostgreSQL to provide a database-backed foundation for reliability validation, SQL practice, API/database consistency checks, and future database-backed performance testing.

The schema uses synthetic healthcare-style data. It is intentionally small, deterministic, and designed for project-scale validation. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## Database

Database name:

    sdet_reliability

Docker Compose service:

    postgres

Container name:

    sdet-postgres

PostgreSQL image:

    postgres:16

## Schema Files

Schema initialization files are located in:

    database/init

The current initialization files are:

    001_create_schema.sql
    002_seed_data.sql

These files are mounted into the PostgreSQL container at:

    /docker-entrypoint-initdb.d

PostgreSQL runs these files automatically when the database volume is first created.

## Tables

The schema currently includes eight relational tables:

| Table | Purpose |
|---|---|
| patients | Stores synthetic patient records |
| facilities | Stores synthetic facility records |
| providers | Stores synthetic provider records |
| encounters | Stores synthetic patient encounters |
| diagnoses | Stores diagnosis lookup/reference records |
| encounter_diagnoses | Bridge table linking encounters to diagnoses |
| lab_orders | Stores synthetic lab orders |
| lab_results | Stores synthetic lab results tied to lab orders |

## Relationship Overview

The schema supports several common relational patterns:

- One patient can have many encounters.
- One facility can have many providers.
- One facility can have many encounters.
- One provider can have many encounters.
- One encounter can have many diagnoses.
- One diagnosis can appear on many encounters.
- One encounter can have many lab orders.
- One lab order can have many lab results.

The encounter_diagnoses table supports a many-to-many relationship between encounters and diagnoses.

## SQL Concepts Supported

This schema supports practice and validation of:

- inner joins
- left joins
- anti-joins
- cross joins / Cartesian joins
- many-to-many joins
- aggregations
- Common Table Expressions
- window functions
- primary keys
- foreign keys
- check constraints
- deterministic seed data
- future query plan analysis
- future index performance comparison

## Local Startup

Start PostgreSQL with:

    docker compose up -d postgres

Check container status with:

    docker compose ps

List tables with:

    docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -c "\dt"

## Seed Data Validation

Expected seed counts:

| Table | Expected Count |
|---|---:|
| patients | 4 |
| encounters | 5 |
| encounter_diagnoses | 5 |

Manual validation examples:

    docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -c "SELECT COUNT(*) AS patient_count FROM patients;"

    docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -c "SELECT COUNT(*) AS encounter_count FROM encounters;"

    docker exec sdet-postgres psql -U sdet_user -d sdet_reliability -c "SELECT COUNT(*) AS encounter_diagnosis_count FROM encounter_diagnoses;"

## SQL Practice Queries

SQL practice and validation queries are stored in:

    database/queries/sql_practice_queries.sql

These queries are intended to support SQL refresh, relational validation, and future database performance work.

## Important Initialization Note

PostgreSQL initialization scripts in docker-entrypoint-initdb.d run only when the database volume is first created.

If schema or seed files are changed later during local development, the local PostgreSQL volume may need to be recreated with:

    docker compose down -v
    docker compose up -d postgres

This removes the local PostgreSQL volume. That is acceptable for this project-scale synthetic database, but it should be treated as destructive behavior.
