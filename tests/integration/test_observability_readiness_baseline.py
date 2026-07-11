import shutil
import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "validate_observability_readiness_baseline.py"


def command_is_available(command: str) -> bool:
    return shutil.which(command) is not None


def docker_engine_is_available() -> bool:
    result = subprocess.run(
        ["docker", "version", "--format", "{{.Server.Version}}"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    return result.returncode == 0


def docker_compose_is_available() -> bool:
    result = subprocess.run(
        ["docker", "compose", "version"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )

    return result.returncode == 0


@pytest.mark.integration
def test_observability_readiness_baseline():
    if not command_is_available("docker"):
        pytest.skip("Docker command is not available in this environment.")

    if not docker_engine_is_available():
        pytest.skip("Docker engine is not available in this environment.")

    if not docker_compose_is_available():
        pytest.skip("Docker Compose is not available in this environment.")

    result = subprocess.run(
        ["python", str(SCRIPT_PATH)],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
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