import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_observability_readiness_baseline.py"

EXPECTED_COMPOSE_SERVICES = {
    "api",
    "postgres",
    "prometheus",
    "grafana",
    "jaeger",
    "otel-collector",
}


def command_is_available(command: str) -> bool:
    return shutil.which(command) is not None


def run_command(command: list[str], timeout_seconds: int = 30) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=timeout_seconds,
        check=False,
    )


def docker_engine_is_available() -> bool:
    result = run_command(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        timeout_seconds=15,
    )

    return result.returncode == 0


def docker_compose_is_available() -> bool:
    result = run_command(
        ["docker", "compose", "version"],
        timeout_seconds=15,
    )

    return result.returncode == 0


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


def expected_observability_stack_is_running() -> bool:
    result = run_command(
        ["docker", "compose", "ps", "--format", "json"],
        timeout_seconds=20,
    )

    if result.returncode != 0:
        return False

    services = parse_json_lines_or_array(result.stdout)

    if not services:
        return False

    observed_services = {
        str(service.get("Service", "")).strip(): str(service.get("State", "")).lower()
        for service in services
        if str(service.get("Service", "")).strip()
    }

    missing_services = EXPECTED_COMPOSE_SERVICES - set(observed_services)

    if missing_services:
        return False

    return all(
        observed_services.get(service) == "running"
        for service in EXPECTED_COMPOSE_SERVICES
    )


@pytest.mark.integration
def test_observability_readiness_baseline():
    if not command_is_available("docker"):
        pytest.skip("Docker command is not available in this environment.")

    if not docker_engine_is_available():
        pytest.skip("Docker engine is not available in this environment.")

    if not docker_compose_is_available():
        pytest.skip("Docker Compose is not available in this environment.")

    if not expected_observability_stack_is_running():
        pytest.skip(
            "Expected observability Docker Compose stack is not running in this environment."
        )

    result = run_command(
        ["python", str(SCRIPT_PATH)],
        timeout_seconds=120,
    )

    output = result.stdout + result.stderr

    assert result.returncode == 0, output

    assert "OBSERVABILITY_READINESS_BASELINE_START" in output
    assert "docker_engine_status | available" in output
    assert "docker_compose_status | available" in output
    assert "docker_compose_expected_services_status | passed" in output
    assert "postgres_readiness_status | passed" in output
    assert "api_health_readiness_status | passed" in output
    assert "prometheus_readiness_readiness_status | passed" in output
    assert "grafana_health_readiness_status | passed" in output
    assert "jaeger_ui_readiness_status | passed" in output
    assert "otel_collector_health_readiness_status | passed" in output
    assert "container_resource_snapshot_status | captured" in output
    assert "observability_scope | readiness only; no trace correlation asserted" in output
    assert "observability_readiness_baseline_status | passed" in output
    assert "OBSERVABILITY_READINESS_BASELINE_COMPLETE" in output