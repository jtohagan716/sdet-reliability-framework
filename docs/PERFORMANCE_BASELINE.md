# Performance Baseline

## Purpose

This project includes a repeatable performance baseline script to measure selected API endpoints under normal local conditions.

The baseline is not a full load test. It is a lightweight evidence artifact used to understand current response-time behavior and compare future changes against a known-good run.

## Agile Testing Context

This work supports the following reliability story:

As a reliability-focused QA/SDET, I want to capture baseline API response-time and error-rate evidence, so that future changes can be compared against a known-good performance profile.

## Acceptance Criteria

- A baseline script sends repeated requests to selected API endpoints.
- The script reports count, passed, failed, average response time, minimum response time, maximum response time, p95 response time, and error rate.
- The baseline covers `/health`, `/patients/1001`, and `/patients/9999`.
- Results are saved in a Markdown report.
- Existing Pytest, Newman, Playwright, and smoke validation checks continue to pass.
- The baseline is documented for repeatable use.

## Baseline Script

Script:

    scripts/run_performance_baseline.py

Default command:

    python .\scripts\run_performance_baseline.py

Default output:

    reports/performance_baseline_v0.6.0.md

Optional arguments:

    --base-url
    --iterations
    --output

Example:

    python .\scripts\run_performance_baseline.py --base-url http://localhost:8000 --iterations 25 --output reports/performance_baseline_custom.md

## Scenarios

The baseline currently covers:

| Scenario | Endpoint | Expected Status |
|---|---|---:|
| health_check | `/health` | 200 |
| patient_lookup_success | `/patients/1001` | 200 |
| patient_lookup_not_found | `/patients/9999` | 404 |

The missing-patient scenario is expected to return `404`. In this baseline, that is treated as a passing result because the API returned the expected behavior.

## Report Fields

The generated report includes:

- `Count`
- `Passed`
- `Failed`
- `Error Rate %`
- `Avg ms`
- `Min ms`
- `Max ms`
- `P95 ms`

## Interpreting Results

A clean baseline should show:

- expected status codes
- zero unexpected failures
- low error rate
- repeatable response-time measurements

A high max or p95 value in a small local run may reflect cold start, local machine load, Docker startup behavior, or temporary resource contention. This is why future performance work should include warm-up runs and more samples.

## Current Baseline Evidence

Current generated report:

    reports/performance_baseline_v0.6.0.md

This report captures a local baseline for `/health`, `/patients/1001`, and `/patients/9999`.

## Reliability Value

This baseline gives testers and engineers evidence for release-readiness and future comparison.

It helps answer:

- Are selected API endpoints returning expected status codes?
- Are there unexpected failures?
- What is the current local response-time profile?
- What is the approximate p95 response time?
- Did a future change make response time worse?

## Future Work

Possible next steps:

- Add warm-up requests.
- Increase sample size.
- Add weighted traffic mix.
- Add lightweight load testing.
- Compare before/after tuning results.
- Add Grafana dashboard screenshots or evidence.
- Define release thresholds for response time and error rate.
