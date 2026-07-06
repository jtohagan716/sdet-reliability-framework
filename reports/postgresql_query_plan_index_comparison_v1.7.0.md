# v1.7.0 - PostgreSQL Patient Lookup Query Plan and Index Comparison

## Summary

This report compares PostgreSQL patient lookup query behavior before and after adding a supporting index for completed patient encounters.

The goal is to demonstrate how data volume and indexing can change PostgreSQL execution strategy.

## Query Under Review

The patient lookup query returns one patient summary and calculates `last_visit` from completed encounters only.

The important access pattern is:

- find one patient by `patient_id`
- find completed encounters for that patient
- calculate the latest completed encounter date

## Baseline Seed Data Result

With the small seed dataset, PostgreSQL used:

| Area | Result |
|---|---|
| Patient lookup | Index Scan using `patients_pkey` |
| Encounter lookup | Sequential Scan on `encounters` |
| Rows removed by filter | 4 |
| Warm-run execution time | approximately 0.133 ms |

This was acceptable because the `encounters` table contained only a few rows.

## Scale Data Setup

A scale-data generator was added to create optional synthetic performance data.

The first scale-data run generated:

| Data Area | Count |
|---|---:|
| Performance patients | 1,000 |
| Performance encounters | 50,000 |
| Completed encounters | 40,000 |
| Scheduled encounters | 10,000 |

The test patient was:

    patient_id = 500999

## Scale Data Result Before Supporting Index

Before adding the supporting index, PostgreSQL used a sequential scan on `encounters`.

Observed behavior:

| Area | Result |
|---|---|
| Encounter access path | Seq Scan on `encounters` |
| Rows returned | 40 |
| Rows removed by filter | 49,965 |
| Buffers | shared hit=438 |
| Execution time | approximately 79.756 ms |

This showed that the query still worked correctly, but the access path became inefficient as encounter volume increased.

## Supporting Index Added

The following partial index was added:

    CREATE INDEX IF NOT EXISTS idx_encounters_completed_patient_date
    ON encounters (patient_id, encounter_date DESC)
    WHERE status = 'completed';

This index supports the patient lookup business rule because `last_visit` is calculated from completed encounters only.

## Scale Data Result After Supporting Index

After adding the index and refreshing PostgreSQL statistics, PostgreSQL changed execution strategy.

Observed behavior:

| Area | Result |
|---|---|
| Encounter access path | Index Only Scan using `idx_encounters_completed_patient_date` |
| Rows returned | 40 |
| Heap Fetches | 0 |
| Buffers | shared hit=4 read=2 |
| Execution time | approximately 0.341 ms |

## Key Delta

| Metric | Before Index | After Index |
|---|---:|---:|
| Encounter access path | Seq Scan | Index Only Scan |
| Rows removed by filter | 49,965 | eliminated from the plan |
| Execution time | ~79.756 ms | ~0.341 ms |
| Heap fetches | not applicable | 0 |

## Interpretation

The original query was fast with tiny seed data because the table was small.

After adding 50,000 encounters, the sequential scan became visibly inefficient because PostgreSQL had to inspect many irrelevant rows to find the completed encounters for one patient.

After adding the partial index, PostgreSQL used an index-only scan. This allowed the database to find the relevant completed encounters directly through the index.

The result demonstrates how data volume, query shape, and index design influence execution strategy.

## Important Note

The exact timing numbers are local development results and should not be treated as production benchmarks.

The important result is the execution strategy change:

    Seq Scan -> Index Only Scan

## Data Safety

All data is synthetic. No real patient data, protected health information, personally identifiable information, credentials, secrets, or production data are used.
