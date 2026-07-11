# Observability Readiness Baseline

## Purpose

The Observability Readiness Baseline validates that the local observability stack is available, reachable, and ready for future trace and metric correlation work.

This release does not claim full tracing, production monitoring, or production-grade observability.

The purpose is to confirm that the required local services are running and accessible before deeper OpenTelemetry, Jaeger, Prometheus, and Grafana integration is added.

## Why This Matters

Reliability work depends on visibility.

Before adding trace correlation or dashboard metrics, the project needs a repeatable way to answer basic readiness questions:

```text
Is Docker available?
Is Docker Compose available?
Are the expected services running?
Is PostgreSQL accepting connections?
Is the API reachable?
Is Prometheus reachable?
Is Grafana reachable?
Is Jaeger reachable?
Is the OpenTelemetry Collector reachable?
Is container resource usage visible?
```

This baseline provides that evidence.

## Scope

This validation covers local development readiness only.

It validates:

* Docker engine availability
* Docker Compose availability
* expected Docker Compose services
* container running state
* container health where available
* container CPU and memory snapshot
* PostgreSQL readiness
* API health endpoint
* Prometheus readiness endpoint
* Grafana health endpoint
* Jaeger UI availability
* OpenTelemetry Collector health endpoint

It does not validate:

* production monitoring
* production alerting
* real patient data
* protected health information
* production traces
* production metrics
* trace correlation
* dashboard correctness
* service-level objectives
* production capacity

## Expected Services

The baseline expects the following Docker Compose services:

```text
api
postgres
prometheus
grafana
jaeger
otel-collector
```

These services represent the local reliability and observability stack for the framework.

## Validation Script

The primary validation script is:

```text
scripts/validate_observability_readiness_baseline.py
```

The script checks Docker, Docker Compose, service readiness, container resource usage, PostgreSQL readiness, and observability endpoints.

Run it manually with:

```powershell
python scripts\validate_observability_readiness_baseline.py
```

## Automated Test

The automated integration test is:

```text
tests/integration/test_observability_readiness_baseline.py
```

Run it with:

```powershell
python -m pytest tests/integration/test_observability_readiness_baseline.py -v
```

The test skips safely if Docker or Docker Compose is not available in the execution environment.

This keeps Continuous Integration/Continuous Delivery (CI/CD) behavior deterministic while still allowing local Docker-backed validation.

## Developer Helper Script

A Windows-friendly PowerShell helper is also included:

```text
scripts/docker_health_summary.ps1
```

Run it with:

```powershell
.\scripts\docker_health_summary.ps1
```

If PowerShell blocks local script execution, run:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\docker_health_summary.ps1
```

This helper provides a readable local summary of:

* Docker Compose services
* container resource usage
* API health
* observability endpoints
* PostgreSQL readiness
* recent API logs
* recent PostgreSQL logs

This script is intended as a developer convenience tool.

The Python validation script remains the primary cross-platform validation artifact.

## Readiness Checks

### Docker Availability

The script checks that the Docker engine is available.

Example evidence:

```text
docker_engine_status | available
docker_engine_version | 29.5.3
```

### Docker Compose Availability

The script checks that Docker Compose is available.

Example evidence:

```text
docker_compose_status | available
docker_compose_version | Docker Compose version v5.1.4
```

### Docker Compose Service Readiness

The script checks that expected services are present and running.

Example evidence:

```text
docker_compose_expected_services_status | passed
api_readiness_status | passed
postgres_readiness_status | passed
prometheus_readiness_status | passed
grafana_readiness_status | passed
jaeger_readiness_status | passed
otel-collector_readiness_status | passed
```

### Container Resource Snapshot

The script captures a one-time Docker resource snapshot.

Example evidence:

```text
CONTAINER_RESOURCE_SNAPSHOT_START
NAME                   CPU %     MEM USAGE / LIMIT     MEM %
sdet-reliability-api   0.89%     57.45MiB / 3.731GiB   1.50%
sdet-otel-collector    1.77%     45.88MiB / 3.731GiB   1.20%
sdet-jaeger            0.22%     228.4MiB / 3.731GiB   5.98%
sdet-grafana           2.19%     196.6MiB / 3.731GiB   5.15%
sdet-prometheus        0.04%     27.58MiB / 3.731GiB   0.72%
sdet-postgres          0.00%     109.1MiB / 3.731GiB   2.86%
container_resource_snapshot_status | captured
CONTAINER_RESOURCE_SNAPSHOT_COMPLETE
```

This is a point-in-time local development snapshot, not a production capacity measurement.

### PostgreSQL Readiness

The script validates PostgreSQL readiness with `pg_isready`.

Example evidence:

```text
postgres_readiness_status | passed
postgres_readiness_output | /var/run/postgresql:5432 - accepting connections
```

### API Health

The script validates the API health endpoint.

Example evidence:

```text
api_health_url | http://localhost:8000/health
api_health_http_status | 200
api_health_readiness_status | passed
```

### Prometheus Readiness

The script validates the Prometheus readiness endpoint.

Example evidence:

```text
prometheus_readiness_url | http://localhost:9090/-/ready
prometheus_readiness_http_status | 200
prometheus_readiness_readiness_status | passed
```

### Grafana Health

The script validates the Grafana health endpoint.

Example evidence:

```text
grafana_health_url | http://localhost:3000/api/health
grafana_health_http_status | 200
grafana_health_readiness_status | passed
```

### Jaeger Availability

The script validates that the Jaeger UI is reachable.

Example evidence:

```text
jaeger_ui_url | http://localhost:16686/
jaeger_ui_http_status | 200
jaeger_ui_readiness_status | passed
```

### OpenTelemetry Collector Health

The script validates the OpenTelemetry Collector health endpoint.

Example evidence:

```text
otel_collector_health_url | http://localhost:13133/
otel_collector_health_http_status | 200
otel_collector_health_readiness_status | passed
```

## Expected Summary Output

A successful run ends with:

```text
observability_scope | readiness only; no trace correlation asserted
observability_stack_components | api, postgres, prometheus, grafana, jaeger, otel-collector
observability_readiness_baseline_status | passed
OBSERVABILITY_READINESS_BASELINE_COMPLETE
```

The scope line is important.

This release confirms readiness only. It does not claim that API requests, database calls, or queue processing are fully traced yet.

## Relationship to Earlier Releases

This release builds on the prior reliability and performance sequence:

```text
v2.5.0 — Query Performance Baseline Validation
v2.6.0 — Query Performance Tuning Comparison
v2.7.0 — API Endpoint Performance Baseline
v2.8.0 — Queue Performance Metrics Baseline
v2.9.0 — Reliability Health Summary Report
```

Those releases created reliability evidence across database behavior, API behavior, queue health, and consolidated reporting.

The Observability Readiness Baseline prepares the project for the next stage:

```text
connect reliability evidence to observability tooling
```

## Why This Is a Baseline

A baseline captures the current expected readiness state.

This gives future releases something to compare against.

Later observability work can build on this foundation by adding:

* API trace correlation
* database span evidence
* queue operation spans
* Prometheus metrics
* Grafana dashboard panels
* saved reliability report artifacts
* CI artifact publishing

## Reliability Value

This release adds value by making the local observability environment easier to inspect and validate.

It provides:

* readable Docker service evidence
* container resource visibility
* endpoint readiness evidence
* PostgreSQL readiness evidence
* explicit observability stack status
* automated pytest coverage
* safe local developer diagnostics
* clear scope boundaries before deeper tracing work

## Summary

The Observability Readiness Baseline confirms that the local observability stack is running and reachable.

It establishes a clean foundation for future OpenTelemetry, Jaeger, Prometheus, and Grafana work.

This release is intentionally limited to readiness validation.

Trace correlation and metric instrumentation will be added in later releases.
