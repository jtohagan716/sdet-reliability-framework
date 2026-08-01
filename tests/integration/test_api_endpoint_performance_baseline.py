import json
import shutil
import subprocess
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "validate_api_endpoint_performance_baseline.py"


def docker_is_available() -> bool:
    return shutil.which("docker") is not None


def postgres_service_is_available() -> bool:
    result = subprocess.run(
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
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    return result.returncode == 0


def api_service_is_available() -> bool:
    try:
        with urlopen(
            "http://localhost:8000/health",
            timeout=5,
        ) as response:
            status_code = response.status
            payload = json.load(response)
    except (OSError, URLError, ValueError):
        return False

    return status_code == 200 and payload.get("status") == "UP"


@pytest.mark.integration
def test_api_endpoint_performance_baseline_validation():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    if not api_service_is_available():
        pytest.skip("API service is not available at http://localhost:8000.")

    assert VALIDATION_SCRIPT.exists(), f"Validation script not found: {VALIDATION_SCRIPT}"

    result = subprocess.run(
        [
            "python",
            str(VALIDATION_SCRIPT),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "API_ENDPOINT_PERFORMANCE_BASELINE_START" in output
    assert "Seeded synthetic API performance baseline review items." in output
    assert "Warm-up requests starting..." in output
    assert "Warm-up requests complete." in output
    assert "Collecting API endpoint performance samples..." in output
    assert "API endpoint performance summary:" in output

    assert "health_endpoint_request_count | 20" in output
    assert "health_endpoint_status_codes | [200]" in output
    assert "health_endpoint_latency_ms_min |" in output
    assert "health_endpoint_latency_ms_mean |" in output
    assert "health_endpoint_latency_ms_median |" in output
    assert "health_endpoint_latency_ms_p95 |" in output
    assert "health_endpoint_latency_ms_max |" in output
    assert "health_endpoint_payload_bytes_min |" in output
    assert "health_endpoint_payload_bytes_max |" in output

    assert "review_list_endpoint_request_count | 20" in output
    assert "review_list_endpoint_status_codes | [200]" in output
    assert "review_list_endpoint_latency_ms_min |" in output
    assert "review_list_endpoint_latency_ms_mean |" in output
    assert "review_list_endpoint_latency_ms_median |" in output
    assert "review_list_endpoint_latency_ms_p95 |" in output
    assert "review_list_endpoint_latency_ms_max |" in output
    assert "review_list_endpoint_payload_bytes_min |" in output
    assert "review_list_endpoint_payload_bytes_max |" in output

    assert "health_status_code_assertion | passed" in output
    assert "review_list_status_code_assertion | passed" in output
    assert "review_list_payload_assertion | passed" in output
    assert "performance_metrics_captured_assertion | passed" in output

    assert (
        "performance_threshold_note | No hard latency threshold is enforced in this baseline."
        in output
    )

    assert "Cleaned up synthetic API performance baseline review items." in output
    assert "API_ENDPOINT_PERFORMANCE_BASELINE_COMPLETE" in output