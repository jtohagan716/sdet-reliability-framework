import json
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]


EXPECTED_COMPOSE_SERVICES = [
    "api",
    "postgres",
    "prometheus",
    "grafana",
    "jaeger",
    "otel-collector",
]


OBSERVABILITY_ENDPOINTS = [
    {
        "name": "api_health",
        "label": "API Health",
        "url": "http://localhost:8000/health",
    },
    {
        "name": "prometheus_readiness",
        "label": "Prometheus Readiness",
        "url": "http://localhost:9090/-/ready",
    },
    {
        "name": "grafana_health",
        "label": "Grafana Health",
        "url": "http://localhost:3000/api/health",
    },
    {
        "name": "jaeger_ui",
        "label": "Jaeger UI",
        "url": "http://localhost:16686/",
    },
    {
        "name": "otel_collector_health",
        "label": "OpenTelemetry Collector Health",
        "url": "http://localhost:13133/",
    },
]


def run_command(command: list[str], timeout_seconds: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def emit(key: str, value: Any) -> None:
    print(f"{key} | {value}")


def section(title: str) -> None:
    print("")
    print(title)
    print("-" * len(title))


def parse_json_lines_or_array(raw_output: str) -> list[dict[str, Any]]:
    raw_output = raw_output.strip()

    if not raw_output:
        return []

    try:
        parsed = json.loads(raw_output)
        if isinstance(parsed, list):
            return parsed
        if isinstance(parsed, dict):
            return [parsed]
    except json.JSONDecodeError:
        pass

    rows: list[dict[str, Any]] = []

    for line in raw_output.splitlines():
        line = line.strip()
        if not line:
            continue

        try:
            parsed_line = json.loads(line)
            if isinstance(parsed_line, dict):
                rows.append(parsed_line)
        except json.JSONDecodeError:
            continue

    return rows


def docker_is_available() -> bool:
    result = run_command(["docker", "version", "--format", "{{.Server.Version}}"], timeout_seconds=15)

    if result.returncode == 0:
        emit("docker_engine_status", "available")
        emit("docker_engine_version", result.stdout.strip())
        return True

    emit("docker_engine_status", "unavailable")
    emit("docker_engine_error", (result.stderr or result.stdout).strip())
    return False


def docker_compose_is_available() -> bool:
    result = run_command(["docker", "compose", "version"], timeout_seconds=15)

    if result.returncode == 0:
        emit("docker_compose_status", "available")
        emit("docker_compose_version", result.stdout.strip())
        return True

    emit("docker_compose_status", "unavailable")
    emit("docker_compose_error", (result.stderr or result.stdout).strip())
    return False


def collect_compose_services() -> tuple[bool, list[dict[str, Any]]]:
    result = run_command(["docker", "compose", "ps", "--format", "json"], timeout_seconds=20)

    if result.returncode != 0:
        emit("docker_compose_ps_status", "failed")
        emit("docker_compose_ps_error", (result.stderr or result.stdout).strip())
        return False, []

    services = parse_json_lines_or_array(result.stdout)

    emit("docker_compose_ps_status", "passed")
    emit("docker_compose_service_count", len(services))

    return True, services


def evaluate_compose_services(services: list[dict[str, Any]]) -> bool:
    observed_services = {
        str(service.get("Service", "")).strip(): service
        for service in services
        if str(service.get("Service", "")).strip()
    }

    all_expected_services_ready = True

    print("")
    print("COMPOSE_SERVICE_SUMMARY_START")

    for expected_service in EXPECTED_COMPOSE_SERVICES:
        service = observed_services.get(expected_service)

        if service is None:
            emit(f"{expected_service}_service_status", "missing")
            all_expected_services_ready = False
            continue

        name = service.get("Name", "")
        state = str(service.get("State", "")).lower()
        status = service.get("Status", "")
        health = str(service.get("Health", "")).lower()

        emit(f"{expected_service}_container_name", name)
        emit(f"{expected_service}_container_state", state)
        emit(f"{expected_service}_container_status", status)

        if health:
            emit(f"{expected_service}_container_health", health)

        if state != "running":
            all_expected_services_ready = False
            emit(f"{expected_service}_readiness_status", "failed")
        else:
            emit(f"{expected_service}_readiness_status", "passed")

    print("COMPOSE_SERVICE_SUMMARY_COMPLETE")

    emit(
        "docker_compose_expected_services_status",
        "passed" if all_expected_services_ready else "failed",
    )

    return all_expected_services_ready


def print_resource_snapshot() -> None:
    result = run_command(
        [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.MemPerc}}",
        ],
        timeout_seconds=30,
    )

    print("")
    print("CONTAINER_RESOURCE_SNAPSHOT_START")

    if result.returncode == 0:
        print(result.stdout.strip())
        emit("container_resource_snapshot_status", "captured")
    else:
        emit("container_resource_snapshot_status", "failed")
        emit("container_resource_snapshot_error", (result.stderr or result.stdout).strip())

    print("CONTAINER_RESOURCE_SNAPSHOT_COMPLETE")


def check_http_endpoint(endpoint: dict[str, str]) -> bool:
    request = urllib.request.Request(
        endpoint["url"],
        headers={"User-Agent": "sdet-reliability-observability-readiness"},
    )

    try:
        with urllib.request.urlopen(request, timeout=8) as response:
            status_code = response.getcode()
            body = response.read(300).decode("utf-8", errors="replace").replace("\n", " ")

            emit(f"{endpoint['name']}_url", endpoint["url"])
            emit(f"{endpoint['name']}_http_status", status_code)

            if body:
                emit(f"{endpoint['name']}_response_preview", body[:200])

            if 200 <= status_code < 400:
                emit(f"{endpoint['name']}_readiness_status", "passed")
                return True

            emit(f"{endpoint['name']}_readiness_status", "failed")
            return False

    except urllib.error.HTTPError as error:
        emit(f"{endpoint['name']}_url", endpoint["url"])
        emit(f"{endpoint['name']}_http_status", error.code)
        emit(f"{endpoint['name']}_readiness_status", "failed")
        return False

    except Exception as error:
        emit(f"{endpoint['name']}_url", endpoint["url"])
        emit(f"{endpoint['name']}_error", str(error))
        emit(f"{endpoint['name']}_readiness_status", "failed")
        return False


def check_observability_endpoints() -> bool:
    print("")
    print("OBSERVABILITY_ENDPOINT_SUMMARY_START")

    endpoint_results = []

    for endpoint in OBSERVABILITY_ENDPOINTS:
        emit("observability_endpoint_check", endpoint["label"])
        endpoint_results.append(check_http_endpoint(endpoint))

    print("OBSERVABILITY_ENDPOINT_SUMMARY_COMPLETE")

    all_endpoints_ready = all(endpoint_results)

    emit(
        "observability_endpoint_readiness_status",
        "passed" if all_endpoints_ready else "failed",
    )

    return all_endpoints_ready


def check_postgres_readiness() -> bool:
    result = run_command(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "pg_isready",
            "-U",
            "sdet_user",
            "-d",
            "sdet_reliability",
        ],
        timeout_seconds=20,
    )

    if result.returncode == 0:
        emit("postgres_readiness_status", "passed")
        emit("postgres_readiness_output", result.stdout.strip())
        return True

    emit("postgres_readiness_status", "failed")
    emit("postgres_readiness_error", (result.stderr or result.stdout).strip())
    return False


def main() -> int:
    print("OBSERVABILITY_READINESS_BASELINE_START")

    section("Docker Availability")
    docker_ready = docker_is_available()
    compose_ready = docker_compose_is_available()

    if not docker_ready or not compose_ready:
        emit("observability_readiness_baseline_status", "failed")
        print("OBSERVABILITY_READINESS_BASELINE_COMPLETE")
        return 1

    section("Docker Compose Service Readiness")
    compose_ps_ready, services = collect_compose_services()
    compose_services_ready = evaluate_compose_services(services) if compose_ps_ready else False

    section("Container Resource Snapshot")
    print_resource_snapshot()

    section("PostgreSQL Readiness")
    postgres_ready = check_postgres_readiness()

    section("Observability Endpoint Readiness")
    endpoints_ready = check_observability_endpoints()

    overall_status = all(
        [
            docker_ready,
            compose_ready,
            compose_ps_ready,
            compose_services_ready,
            postgres_ready,
            endpoints_ready,
        ]
    )

    section("Observability Readiness Summary")
    emit("observability_scope", "readiness only; no trace correlation asserted")
    emit("observability_stack_components", "api, postgres, prometheus, grafana, jaeger, otel-collector")
    emit("observability_readiness_baseline_status", "passed" if overall_status else "failed")

    print("OBSERVABILITY_READINESS_BASELINE_COMPLETE")

    return 0 if overall_status else 1


if __name__ == "__main__":
    sys.exit(main())