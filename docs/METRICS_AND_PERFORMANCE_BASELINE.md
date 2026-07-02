# Metrics and Performance Baseline

## Purpose

This project exposes Prometheus metrics to make API behavior measurable during local validation, smoke testing, CI review, and future performance analysis.

Diagnostic logs tell us what happened during a request.
Request IDs let us trace one request across log lines.
Metrics let us measure behavior over time.

## Agile Testing Context

This work supports the following reliability story:

As a reliability-focused QA/SDET, I want API behavior exposed through metrics, so that request volume, response outcomes, and latency can be measured during validation and performance analysis.

## Acceptance Criteria

- The API exposes HTTP request counters through `/metrics`.
- The API records request duration through Prometheus histogram metrics.
- Metrics include method, path, and status code labels.
- Synthetic patient lookup success and not-found outcomes are counted.
- Metrics avoid high-cardinality labels where possible.
- Existing API behavior remains unchanged.
- Pytest, Newman, and local smoke validation checks continue to pass.

## Metrics Added

### HTTP Request Count

Metric:

    sdet_http_requests_total

Purpose:

Counts HTTP requests by method, route path, and status code.

Example:

    sdet_http_requests_total{method="GET",path="/patients/{patient_id}",status_code="200"} 1.0
    sdet_http_requests_total{method="GET",path="/patients/{patient_id}",status_code="404"} 1.0

### HTTP Request Duration

Metric:

    sdet_http_request_duration_seconds

Purpose:

Records request duration using Prometheus histogram buckets.

Useful values include:

    sdet_http_request_duration_seconds_bucket
    sdet_http_request_duration_seconds_count
    sdet_http_request_duration_seconds_sum

These can support future latency analysis, including average response time and percentile-based performance review.

### Patient Lookup Outcomes

Metric:

    sdet_patient_lookup_total

Purpose:

Counts synthetic patient lookup outcomes.

Example:

    sdet_patient_lookup_total{outcome="success"} 1.0
    sdet_patient_lookup_total{outcome="not_found"} 1.0

## High-Cardinality Label Control

The API uses route templates for metric path labels.

Preferred metric label:

    path="/patients/{patient_id}"

Avoided metric labels:

    path="/patients/1001"
    path="/patients/9999"

This matters because metrics systems such as Prometheus perform better when labels have controlled, predictable values.

Logs may include exact request paths and IDs for troubleshooting.
Metrics should use stable route patterns for measurement.

## Manual Validation

The following endpoints were used to generate metrics:

    GET /health
    GET /patients/1001
    GET /patients/9999
    GET /metrics

Expected behavior:

- `/health` returns `200`.
- `/patients/1001` returns `200`.
- `/patients/9999` returns `404`.
- `/metrics` includes the new SDET reliability metrics.

## Automated Validation

Metrics are validated by:

    tests/test_metrics_observability.py

The tests confirm that:

- HTTP request count metrics are exposed.
- Patient route labels use `/patients/{patient_id}` instead of specific patient IDs.
- Patient lookup success and not-found outcomes are counted.
- Request duration histogram metrics are exposed.

## Release-Readiness Value

These metrics support release-readiness by giving testers and engineers measurable evidence about API behavior.

They help answer questions such as:

- Are requests reaching the API?
- Which status codes are being returned?
- Are successful and not-found patient lookups counted?
- How long are requests taking?
- Are metrics labels stable and dashboard-friendly?

## Future Performance Baseline Work

This is the foundation for future performance baseline work.

Possible next steps:

- Capture baseline response-time results.
- Track average and percentile response times.
- Add lightweight load testing.
- Compare before/after tuning results.
- Create Grafana dashboard evidence.
- Define release quality thresholds for response time and error rate.
