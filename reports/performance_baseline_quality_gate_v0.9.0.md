# Performance Baseline Report

Generated UTC: `2026-07-03T16:02:13.775107+00:00`
Base URL: `http://localhost:8000`
Iterations per scenario: `10`

## Summary

| Scenario | Path | Expected Status | Count | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| health_check | `/health` | 200 | 10 | 10 | 0 | 0.0 | 279.54 | 8.31 | 2504.85 | 2504.85 |
| patient_lookup_success | `/patients/1001` | 200 | 10 | 10 | 0 | 0.0 | 46.44 | 15.7 | 133.04 | 133.04 |
| patient_lookup_not_found | `/patients/9999` | 404 | 10 | 10 | 0 | 0.0 | 32.2 | 14.6 | 56.05 | 56.05 |

## Interpretation

This report captures a local baseline for selected API paths.

- `passed` means the endpoint returned the expected HTTP status code.
- `failed` means the endpoint returned an unexpected result or could not be reached.
- `p95_ms` represents the approximate 95th percentile response time for the scenario.
- This is not a full load test. It is a repeatable local baseline used for comparison against future changes.

## Reliability Value

This baseline helps compare future behavior against a known-good local run. It supports performance regression detection, release-readiness review, and troubleshooting conversations.
