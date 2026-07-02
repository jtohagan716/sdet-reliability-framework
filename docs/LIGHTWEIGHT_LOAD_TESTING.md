# Lightweight Load Testing

## Purpose

This project includes a lightweight load testing script to exercise selected API endpoints using a controlled weighted traffic mix.

The goal is not to perform a full enterprise-scale load test. The goal is to create repeatable local evidence about API behavior under small concurrent traffic.

This builds on the previous performance baseline work.

## Baseline vs Load Test

A performance baseline asks:

    What does normal look like right now?

A lightweight load test asks:

    How does the API behave under a small expected traffic mix?

The baseline sends repeated requests to selected endpoints. The load test introduces weighted traffic and concurrency.

## Agile Testing Context

This work supports the following reliability story:

As a reliability-focused QA/SDET, I want to run a lightweight load test using a weighted API traffic mix, so that I can evaluate response time, error rate, throughput, and scenario outcomes before release.

## Acceptance Criteria

- A load test script sends requests using a weighted traffic mix.
- The test covers successful, not-found, invalid-input, and health-check scenarios.
- The script supports configurable total requests, concurrency, base URL, seed, and output path.
- The report includes total requests, passed, failed, error rate, average response time, min, max, p95, p99, elapsed time, and requests per second.
- Scenario-level results are included.
- Expected `404` and `422` responses are treated as passing when they match the scenario expectation.
- The script is covered by automated Pytest tests.
- Existing Pytest, Newman, Playwright, and smoke validation checks continue to pass.

## Script

Script:

    scripts/run_lightweight_load_test.py

Default command:

    python .\scripts\run_lightweight_load_test.py

Default output:

    reports/lightweight_load_test_v0.7.0.md

## Default Traffic Mix

| Scenario | Endpoint | Expected Status | Weight |
|---|---|---:|---:|
| patient_lookup_primary_success | `/patients/1001` | 200 | 60 |
| patient_lookup_secondary_success | `/patients/1002` | 200 | 20 |
| patient_lookup_not_found | `/patients/9999` | 404 | 10 |
| patient_lookup_invalid_id | `/patients/abc` | 422 | 5 |
| health_check | `/health` | 200 | 5 |

This means the test simulates mostly successful patient lookups, with a smaller number of not-found, invalid-input, and health-check requests.

## Example Commands

Run the default load test:

    python .\scripts\run_lightweight_load_test.py

Run with more requests:

    python .\scripts\run_lightweight_load_test.py --total-requests 250

Run with different concurrency:

    python .\scripts\run_lightweight_load_test.py --total-requests 250 --concurrency 10

Run against a custom base URL:

    python .\scripts\run_lightweight_load_test.py --base-url http://localhost:8000

Write to a custom report file:

    python .\scripts\run_lightweight_load_test.py --output reports/lightweight_load_test_custom.md

## Report Fields

The generated report includes:

- `Total Requests`
- `Passed`
- `Failed`
- `Error Rate %`
- `Avg ms`
- `Min ms`
- `Max ms`
- `P95 ms`
- `P99 ms`
- `Elapsed sec`
- `Requests/sec`

## Interpreting Results

A clean lightweight load test should show:

- all requests returning expected status codes
- zero unexpected failures
- low error rate
- reasonable response times
- scenario-level visibility
- repeatable results across local runs

Expected errors can still be passing test outcomes.

For example:

- `/patients/9999` should return `404`
- `/patients/abc` should return `422`

Those are passing outcomes because the API is behaving as expected.

## Tail Latency

The report includes p95 and p99 response times.

Average response time can hide slow outliers. Tail latency helps show whether a small percentage of requests were much slower than the rest.

For example, a test may show:

    avg_ms = 339
    p95_ms = 350
    p99_ms = 5505

This means most requests were relatively fast, but at least one request was much slower. In a local Docker environment, that may be caused by cold start, resource contention, local machine load, or container scheduling.

The correct response is not panic. The correct response is investigation.

## Reliability Value

This load test provides release-readiness evidence.

It helps answer:

- Did the API return expected results under concurrent traffic?
- Were there unexpected failures?
- What was the observed throughput?
- What was the average response time?
- Were there slow tail-latency outliers?
- Which scenarios were slower or more failure-prone?

## Future Work

Possible next steps:

- Add a warm-up phase.
- Compare load test results against the baseline.
- Add pass/fail thresholds for p95 and error rate.
- Add a larger sustained load profile.
- Add Grafana dashboard evidence during load.
- Add Kubernetes-based deployment validation.
- Add CI quality-gate documentation for performance checks.
