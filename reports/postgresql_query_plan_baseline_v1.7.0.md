# v1.7.0 Baseline - PostgreSQL Patient Lookup Query Plan

## Summary

This report captures the baseline PostgreSQL query plan for the patient lookup API before adding a supporting patient lookup index or scale-data experiment.

The baseline is intentionally captured before optimization changes so that later results can be compared against the original execution strategy.

## Baseline Query

The patient lookup query returns one patient summary and calculates `last_visit` from completed encounters only.

Patient `1004` is used because it supports the completed-versus-scheduled encounter business rule.

## Current Indexes

The baseline database includes primary-key indexes only.

Relevant indexes:

| Table | Index | Column |
|---|---|---|
| patients | patients_pkey | patient_id |
| encounters | encounters_pkey | encounter_id |

There is currently no supporting index on:

- encounters.patient_id
- encounters.status
- encounters.encounter_date

## Observed Baseline Plan

Observed plan characteristics:

| Plan Area | Baseline Behavior |
|---|---|
| Patient lookup | Index Scan using `patients_pkey` |
| Encounter lookup | Sequential Scan on `encounters` |
| Join type | Nested Loop Left Join |
| Aggregation | GroupAggregate |
| Rows removed by encounter filter | 4 |
| Buffers | shared hit=3 |
| Warm-run planning time | approximately 0.411 ms |
| Warm-run execution time | approximately 0.133 ms |

## Interpretation

The patient lookup uses the primary-key index and is healthy.

The encounter lookup uses a sequential scan. This is acceptable for the tiny baseline seed dataset because the table contains only a few rows.

The scalability risk is that the same access pattern could become inefficient as the `encounters` table grows.

## Performance Implication

The API endpoint is fast at baseline because the dataset is small.

The baseline does not prove that the query access path will scale.

A supporting index should be evaluated for the query pattern:

- patient_id lookup
- completed encounters only
- latest completed encounter date

## Candidate Index

A candidate partial index is:

    CREATE INDEX IF NOT EXISTS idx_encounters_completed_patient_date
    ON encounters (patient_id, encounter_date DESC)
    WHERE status = 'completed';

This index matches the business rule that `last_visit` is calculated from completed encounters only.

## Next Step

The next step is to add a controlled scale-data generator and compare query plans at larger encounter row counts before and after adding the supporting index.

## Scope

This report captures baseline behavior only.

It does not claim production performance results.

All data is synthetic.
