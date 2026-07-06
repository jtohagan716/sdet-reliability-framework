# PostgreSQL Query Plan and Index Validation

## Purpose

This document captures and explains the PostgreSQL query plan behind the patient lookup API.

The goal is to understand how PostgreSQL executes the patient lookup query, how the execution strategy changes as data volume grows, and how indexes can support scalable API behavior.

This validation area connects API behavior, database access patterns, query planning, indexing, and performance implications.

## Patient Lookup Query

The patient lookup API uses a query shaped like this:

    SELECT
        p.patient_id,
        p.first_name || ' ' || p.last_name AS name,
        p.status,
        COALESCE(TO_CHAR(MAX(e.encounter_date), 'YYYY-MM-DD'), '') AS last_visit
    FROM patients p
    LEFT JOIN encounters e
        ON p.patient_id = e.patient_id
       AND e.status = 'completed'
    WHERE p.patient_id = 1004
    GROUP BY
        p.patient_id,
        p.first_name,
        p.last_name,
        p.status;

The query returns one patient summary and calculates the latest completed encounter date.

## Business Rule

The `last_visit` value must be calculated from completed encounters only.

Scheduled and cancelled encounters should not be used for `last_visit`.

Patient `1004` is useful for this validation because the synthetic database includes both completed and scheduled encounter data for that patient.

## Baseline Indexes

The current baseline includes primary-key indexes only.

Observed indexes include:

    patients_pkey
    encounters_pkey
    facilities_pkey
    providers_pkey
    diagnoses_pkey
    encounter_diagnoses_pkey
    lab_orders_pkey
    lab_results_pkey

The `patients` table has a primary-key index on:

    patients.patient_id

The `encounters` table has a primary-key index on:

    encounters.encounter_id

At baseline, there is no supporting index on:

    encounters.patient_id
    encounters.status
    encounters.encounter_date

## Baseline Query Plan Summary

With the small seed dataset, PostgreSQL uses:

| Plan Area | Observed Behavior |
|---|---|
| Patient lookup | Index Scan using `patients_pkey` |
| Encounter lookup | Sequential Scan on `encounters` |
| Join type | Nested Loop Left Join |
| Aggregation | GroupAggregate |
| Rows removed by encounter filter | 4 |
| Warm-run execution time | approximately 0.133 ms |

## Interpretation

The patient side of the query is healthy because PostgreSQL uses the primary-key index on `patients.patient_id`.

The encounter side currently uses a sequential scan. With only a few seed rows, this is acceptable and efficient enough.

The important performance implication is that the sequential scan can become risky as the `encounters` table grows.

With a larger dataset, PostgreSQL may need to inspect many encounter rows to find the completed encounters for one patient unless an index supports the access pattern.

## Why Sequential Scan Is Not Automatically Bad

A sequential scan is not always a problem.

For tiny tables, PostgreSQL may correctly decide that scanning the whole table is cheaper than using an index.

The performance concern appears when the table grows and the query still needs only a small subset of rows.

## Index Direction

The patient lookup query needs this access pattern:

    one patient
    completed encounters only
    latest encounter date

A supporting index should match that query shape and business rule.

A strong candidate is a partial index:

    CREATE INDEX IF NOT EXISTS idx_encounters_completed_patient_date
    ON encounters (patient_id, encounter_date DESC)
    WHERE status = 'completed';

This index focuses only on completed encounters and orders encounter dates so the latest completed visit can be found efficiently.

## Validation Strategy

This milestone should validate:

- baseline query plan behavior
- existing indexes
- query correctness before index changes
- optional scale-data behavior at larger row counts
- supporting index existence
- query behavior after index creation
- API-to-database consistency remains intact

## Important Note About Optimizer Behavior

The validation should not require PostgreSQL to always use the index.

PostgreSQL is a cost-based optimizer. It may still choose a sequential scan for tiny datasets.

A professional validation should confirm that the index exists, the query remains correct, and the query plan can be captured and reviewed.

For scale-data experiments, the project can demonstrate whether PostgreSQL changes execution strategy as row counts increase.

## Scope

This milestone focuses on read-only query-plan and index validation.

It does not add production tuning recommendations, production data, database migrations, or real patient data.

## Data Safety

All data is synthetic. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.
