# Lightweight Load Test Report

Generated UTC: `2026-07-02T21:29:33.547670+00:00`
Base URL: `http://localhost:8000`
Total Requests: `100`
Concurrency: `5`
Traffic Seed: `7`

## Overall Summary

| Total Requests | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms | P99 ms | Elapsed sec | Requests/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 100 | 0 | 0.0 | 339.15 | 10.74 | 5511.92 | 350.69 | 5505.52 | 6.83 | 14.65 |

## Scenario Breakdown

| Scenario | Path | Expected Status | Weight | Count | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| patient_lookup_primary_success | `/patients/1001` | 200 | 60 | 60 | 60 | 0 | 0.0 | 248.84 | 12.92 | 5511.92 | 322.41 |
| patient_lookup_secondary_success | `/patients/1002` | 200 | 20 | 20 | 20 | 0 | 0.0 | 348.15 | 13.13 | 5489.2 | 350.69 |
| patient_lookup_not_found | `/patients/9999` | 404 | 10 | 10 | 10 | 0 | 0.0 | 596.31 | 10.74 | 5283.6 | 5283.6 |
| patient_lookup_invalid_id | `/patients/abc` | 422 | 5 | 5 | 5 | 0 | 0.0 | 95.57 | 12.87 | 343.8 | 343.8 |
| health_check | `/health` | 200 | 5 | 5 | 5 | 0 | 0.0 | 1116.15 | 61.85 | 5277.29 | 5277.29 |

## Interpretation

This report captures a lightweight local load test using a weighted traffic mix.

- `passed` means the endpoint returned the expected HTTP status code.
- `failed` means the endpoint returned an unexpected status code or could not be reached.
- `404` and `422` can be passing results when they are the expected behavior for the scenario.
- `p95_ms` shows the approximate 95th percentile response time.
- `requests_per_second` shows observed local throughput during the run.

## Reliability Value

This load test provides evidence about API behavior under a small controlled traffic mix. It helps compare expected behavior, response time, error rate, and throughput against the previous baseline.
