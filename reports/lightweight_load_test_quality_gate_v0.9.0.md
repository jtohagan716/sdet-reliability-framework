# Lightweight Load Test Report

Generated UTC: `2026-07-03T16:02:16.900437+00:00`
Base URL: `http://localhost:8000`
Total Requests: `100`
Concurrency: `5`
Traffic Seed: `7`

## Overall Summary

| Total Requests | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms | P99 ms | Elapsed sec | Requests/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 100 | 0 | 0.0 | 72.45 | 9.6 | 291.44 | 239.66 | 289.49 | 1.47 | 67.93 |

## Scenario Breakdown

| Scenario | Path | Expected Status | Weight | Count | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| patient_lookup_primary_success | `/patients/1001` | 200 | 60 | 60 | 60 | 0 | 0.0 | 69.83 | 11.83 | 291.44 | 239.63 |
| patient_lookup_secondary_success | `/patients/1002` | 200 | 20 | 20 | 20 | 0 | 0.0 | 61.65 | 15.46 | 276.66 | 115.46 |
| patient_lookup_not_found | `/patients/9999` | 404 | 10 | 10 | 10 | 0 | 0.0 | 102.28 | 20.8 | 266.94 | 266.94 |
| patient_lookup_invalid_id | `/patients/abc` | 422 | 5 | 5 | 5 | 0 | 0.0 | 83.0 | 16.14 | 207.12 | 207.12 |
| health_check | `/health` | 200 | 5 | 5 | 5 | 0 | 0.0 | 76.79 | 9.6 | 237.95 | 237.95 |

## Interpretation

This report captures a lightweight local load test using a weighted traffic mix.

- `passed` means the endpoint returned the expected HTTP status code.
- `failed` means the endpoint returned an unexpected status code or could not be reached.
- `404` and `422` can be passing results when they are the expected behavior for the scenario.
- `p95_ms` shows the approximate 95th percentile response time.
- `requests_per_second` shows observed local throughput during the run.

## Reliability Value

This load test provides results about API behavior under a small controlled traffic mix. It helps compare expected behavior, response time, error rate, and throughput against the previous baseline.


