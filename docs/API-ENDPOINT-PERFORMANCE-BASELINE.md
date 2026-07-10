# API Endpoint Performance Baseline

## Purpose

The API Endpoint Performance Baseline feature establishes the first repeatable API-layer performance measurement for the SDET Reliability Framework.

This feature extends the project’s performance specialization path beyond PostgreSQL query plans and into real FastAPI endpoint behavior.

The goal is not to tune the API yet.

The goal is to measure endpoint behavior, capture useful metrics, validate functional correctness, and create a trusted baseline that future API tuning or regression checks can compare against.

The guiding principle is:

```text
measure first
avoid premature tuning
capture repeatable metrics
preserve functional correctness
document the evidence honestly
```

## Why This Matters

An endpoint can return `200 OK` and still be trending toward performance risk.

Basic testing answers:

```text
Did the endpoint work?
```

Performance-aware reliability testing asks:

```text
How long did the endpoint take?
How consistent was the response time?
How large was the payload?
Were all responses successful?
Was p95 latency meaningfully higher than the median?
Is this endpoint a future tuning candidate?
```

This feature begins answering those questions with repeatable local API performance evidence.

## Endpoints Measured

The validation measures:

```text
GET /health
GET /qa/data-quality-review-items
```

### GET /health

The health endpoint is expected to be lightweight.

It provides a simple API availability baseline.

### GET /qa/data-quality-review-items

The review list endpoint is expected to be heavier than `/health`.

It exercises application logic, database-backed review data, response serialization, and a larger response payload.

This endpoint is a better candidate for future API/database performance analysis.

## Synthetic Data

The validation script seeds synthetic patient data quality review records before collecting endpoint metrics.

The seeded records use keys beginning with:

```text
dq-api-perf-baseline-review-
```

The synthetic data is used only for local validation.

The script cleans up the seeded records after the run.

## Metrics Captured

The validation captures these metrics for each endpoint:

```text
request count
status codes
minimum latency
mean latency
median latency
p95 latency
maximum latency
minimum payload size
maximum payload size
```

The validation also checks:

```text
health endpoint status code
review list endpoint status code
review list payload evidence
metrics captured assertion
cleanup confirmation
```

## Warm-Up Requests

The script performs warm-up requests before collecting the measured samples.

This is intentional.

Warm-up requests reduce the chance that one-time startup effects dominate the measured baseline.

The warm-up phase is not treated as the measured result.

## Sample Size

The current local baseline uses:

```text
20 measured requests per endpoint
3 warm-up requests per endpoint
```

This is enough to create a small local baseline without turning the validation into a heavy load test.

It is not a production-scale load test.

## Observed Local Baseline Example

One observed local run produced the following results:

```text
Metric                         /health        /qa/data-quality-review-items
Request Count                  20             20
Status Codes                   [200]          [200]
Mean Latency                   37.550 ms      70.775 ms
Median Latency                 35.041 ms      63.175 ms
p95 Latency                    53.283 ms      123.459 ms
Max Latency                    113.754 ms     187.758 ms
Payload Size                   66 bytes       20,645 bytes
```

The review list endpoint was slower than `/health`, which is expected because it returns a much larger payload and exercises application/database-backed behavior.

## Interpretation

The observed baseline shows:

```text
both endpoints returned HTTP 200
metrics were captured successfully
the review list endpoint had higher latency than the health endpoint
the review list endpoint returned a substantially larger payload
p95 latency was higher than median latency
no hard latency threshold was enforced
synthetic data was cleaned up after the run
```

The p95 value is important because average latency alone can hide slower requests.

A future performance regression check can compare against this baseline.

## Why No Hard Timing Threshold Is Used

This feature intentionally does not assert a fixed latency threshold such as:

```text
/qa/data-quality-review-items must always respond in under 100 ms
```

That would be brittle in a local Docker-based environment.

Local response time can vary because of:

```text
Docker Desktop resource state
host machine load
database cache state
API container state
network timing between host and container
Python runtime overhead
first-run effects
CI environment differences
```

Instead, the validation checks that:

```text
requests complete successfully
metrics are captured
payload evidence exists
status codes are valid
cleanup occurs
no hard performance claim is made
```

This creates a stable baseline for future comparison without creating noisy tests.

## Assertions Validated

Expected assertions:

```text
health_status_code_assertion | passed
review_list_status_code_assertion | passed
review_list_payload_assertion | passed
performance_metrics_captured_assertion | passed
API_ENDPOINT_PERFORMANCE_BASELINE_COMPLETE
```

## Manual Validation

Run:

```powershell
python scripts\validate_api_endpoint_performance_baseline.py
```

Expected result:

```text
health_status_code_assertion | passed
review_list_status_code_assertion | passed
review_list_payload_assertion | passed
performance_metrics_captured_assertion | passed
API_ENDPOINT_PERFORMANCE_BASELINE_COMPLETE
```

## Automated Validation

Run the focused API endpoint performance baseline test:

```powershell
python -m pytest tests/integration/test_api_endpoint_performance_baseline.py -v
```

Run the performance validation group:

```powershell
python -m pytest tests/integration/test_query_performance_baseline.py tests/integration/test_query_performance_tuning_comparison.py tests/integration/test_api_endpoint_performance_baseline.py -v
```

Run the full reliability and performance validation group:

```powershell
python -m pytest tests/integration/test_data_quality_work_queue.py tests/integration/test_data_quality_work_queue_retry_dead_letter.py tests/integration/test_query_performance_baseline.py tests/integration/test_query_performance_tuning_comparison.py tests/integration/test_api_endpoint_performance_baseline.py -v
```

## Relationship to Query Performance Work

This feature builds on:

```text
v2.5.0 — Query Performance Baseline Validation
v2.6.0 — Query Performance Tuning Comparison
```

Those releases focused on PostgreSQL query behavior.

This release moves one layer up to API endpoint behavior.

Together, they begin forming an end-to-end performance picture:

```text
database query plan
database timing evidence
API response timing
payload size
status code behavior
future regression comparison
```

## Current Performance Evidence Model

This feature captures API-layer metrics.

The broader performance evidence model will eventually include:

```text
API latency
database query timing
queue depth
retry count
dead-letter count
OpenTelemetry traces
Prometheus metrics
Grafana dashboard panels
container CPU and memory
CI/test runtime
production risk indicators
```

This release does not attempt to capture all of those yet.

It establishes the API endpoint measurement foundation.

## Production Monitoring Candidates

The local validation does not prove production behavior, but it identifies metrics that would be useful in a production-like environment:

```text
API p95 latency
API p99 latency
error rate
payload size growth
request volume
database query duration behind endpoints
queue depth
oldest ready queue item age
dead-letter growth
CPU pressure
memory pressure
context switching where available
```

A useful operational interpretation is:

```text
This metric was not a failure condition in the local validation environment, but it is a production monitoring candidate under higher concurrency or larger data volume.
```

## Reliability and Performance Value

This feature demonstrates:

```text
API endpoint performance baseline discipline
warm-up request handling
repeatable response-time sampling
p95 latency capture
payload size capture
status code validation
functional payload validation
synthetic data cleanup
avoidance of brittle timing thresholds
foundation for future API performance regression checks
```

This is relevant to Software Development Engineer in Test (SDET), Site Reliability Engineering (SRE), application support, production support, healthcare integration testing, and API/database reliability validation roles.

## Scope

This feature uses synthetic healthcare-style data only.

It does not use real patient data, protected health information, production credentials, or production database exports.

It does not claim production-scale API performance results.

It establishes a local repeatable API endpoint performance baseline for future comparison.

## Summary

API Endpoint Performance Baseline adds the first API-layer performance evidence to the project.

It measures `/health` and `/qa/data-quality-review-items`, captures response-time and payload metrics, validates status and payload evidence, cleans up synthetic data, and avoids fragile latency thresholds.

This is the next step in building an end-to-end healthcare data reliability and performance diagnostics portfolio.
