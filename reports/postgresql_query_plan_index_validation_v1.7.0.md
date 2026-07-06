# v1.7.0 - PostgreSQL Query Plan and Index Validation

## Summary

This milestone adds PostgreSQL query plan and index validation for the patient lookup API path.

The goal is to demonstrate how PostgreSQL execution strategy changes based on data volume, query shape, statistics, and index support.

## Added

- Baseline patient lookup query plan documentation
- Patient lookup scale-data generator
- Partial index for completed patient encounters
- Query plan and index comparison report
- CI-safe patient lookup query plan validation script
- GitHub Actions validation step for query plan and index validation

## Query Under Review

The patient lookup query returns one patient summary and calculates `last_visit` from completed encounters only.

The important access pattern is:

- find one patient by `patient_id`
- find completed encounters for that patient
- calculate the latest completed encounter date

## Baseline Behavior

With the small seed dataset, PostgreSQL used:

- `Index Scan` on `patients_pkey`
- `Seq Scan` on `encounters`
- `Nested Loop Left Join`
- `GroupAggregate`

The sequential scan was acceptable for tiny seed data because the `encounters` table contained only a few rows.

## Scale-Data Experiment

A scale-data generator was added to create optional synthetic performance data.

The first local scale-data experiment generated:

- 1,000 synthetic performance patients
- 50,000 synthetic performance encounters
- 40,000 completed encounters
- 10,000 scheduled encounters

Before adding the supporting index, PostgreSQL used a sequential scan on `encounters` and removed 49,965 rows by filter for the tested patient lookup.

## Supporting Index

The following partial index was added:

    CREATE INDEX IF NOT EXISTS idx_encounters_completed_patient_date
    ON encounters (patient_id, encounter_date DESC)
    WHERE status = 'completed';

This index supports the business rule that `last_visit` is calculated from completed encounters only.

## Result After Index

After adding the partial index, PostgreSQL changed execution strategy during the local scale-data experiment:

- before index: `Seq Scan`
- after index: `Index Only Scan`
- heap fetches after index: 0
- execution time dropped from approximately 79.756 ms to approximately 0.341 ms in the local run

The exact timing values are local development results, not production benchmarks.

The important result is the execution strategy change:

    Seq Scan -> Index Only Scan

## CI-Safe Validation

The CI-safe validation script does not require PostgreSQL to always use the index because tiny seed data may still make sequential scans reasonable.

Instead, it validates:

- PostgreSQL container is running
- API container is running
- patient lookup index exists
- index definition includes the expected table, columns, and completed-status predicate
- patient lookup SQL returns the expected latest completed visit
- `EXPLAIN (ANALYZE, BUFFERS)` can be captured
- query plan output includes expected structural markers

## Scope

This milestone demonstrates local query-plan analysis, index validation, and CI-safe query-plan checks.

It does not claim production performance benchmarking.

## Data Safety

All data is synthetic. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.

## Future Improvements

- Add larger local scale-data experiments with multiple data volumes
- Capture query-plan results at 10,000, 100,000, and 1,000,000 encounter rows
- Add before/after comparison automation
- Add database-backed performance baseline checks
- Add controlled defect detection around completed-versus-scheduled encounter logic
