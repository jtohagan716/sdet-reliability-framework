# Lightweight Load Test Report

Generated UTC: `2026-07-07T04:23:50.299994+00:00`
Base URL: `http://localhost:8000`
Total Requests: `100`
Concurrency: `5`
Traffic Seed: `7`

## Overall Summary

| Total Requests | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms | P99 ms | Elapsed sec | Requests/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 100 | 100 | 0 | 0.0 | 164.82 | 8.45 | 730.75 | 459.66 | 723.83 | 3.35 | 29.89 |

## Scenario Breakdown

| Scenario | Path | Expected Status | Weight | Count | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| patient_lookup_primary_success | `/patients/1001` | 200 | 60 | 60 | 60 | 0 | 0.0 | 170.03 | 30.25 | 730.75 | 459.66 |
| patient_lookup_secondary_success | `/patients/1002` | 200 | 20 | 20 | 20 | 0 | 0.0 | 163.67 | 27.99 | 723.83 | 461.19 |
| patient_lookup_not_found | `/patients/9999` | 404 | 10 | 10 | 10 | 0 | 0.0 | 188.45 | 47.05 | 404.51 | 404.51 |
| patient_lookup_invalid_id | `/patients/abc` | 422 | 5 | 5 | 5 | 0 | 0.0 | 109.86 | 8.45 | 365.78 | 365.78 |
| health_check | `/health` | 200 | 5 | 5 | 5 | 0 | 0.0 | 114.64 | 31.49 | 267.75 | 267.75 |

## Interpretation

This report captures a lightweight local load test using a weighted traffic mix.

- `passed` means the endpoint returned the expected HTTP status code.
- `failed` means the endpoint returned an unexpected status code or could not be reached.
- `404` and `422` can be passing results when they are the expected behavior for the scenario.
- `p95_ms` shows the approximate 95th percentile response time.
- `requests_per_second` shows observed local throughput during the run.

## Reliability Value

This load test provides evidence about API behavior under a small controlled traffic mix. It helps compare expected behavior, response time, error rate, and throughput against the previous baseline.
