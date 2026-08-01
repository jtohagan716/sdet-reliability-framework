import json
import shutil
import subprocess
import sys
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SUMMARY_SCRIPT = REPO_ROOT / "scripts" / "generate_reliability_health_summary.py"


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
def test_reliability_health_summary_report():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    if not api_service_is_available():
        pytest.skip("API service is not available at http://localhost:8000.")

    assert SUMMARY_SCRIPT.exists(), f"Summary script not found: {SUMMARY_SCRIPT}"

    result = subprocess.run(
        [
            sys.executable,
            str(SUMMARY_SCRIPT),
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "RELIABILITY_HEALTH_SUMMARY_START" in output
    assert "environment_status | passed" in output
    assert "postgres_service_status | available" in output
    assert "api_service_status | available" in output

    assert "Running query performance baseline validation..." in output
    assert "Running query performance tuning comparison validation..." in output
    assert "Running API endpoint performance baseline validation..." in output
    assert "Running queue performance metrics baseline validation..." in output

    assert "RELIABILITY HEALTH SUMMARY" in output
    assert "summary_scope | synthetic healthcare-style validation only" in output
    assert "summary_safety | rollback-safe validation data" in output
    assert "summary_threshold_policy | no hard local latency threshold enforced" in output
    assert "summary_layer_coverage | database_query, database_tuning, api_endpoint, queue_health" in output

    assert "query_performance_baseline_status | passed" in output
    assert "query_performance_baseline_evidence | baseline_row_count_assertion | passed" in output
    assert "query_performance_baseline_evidence | queue_linkage_assertion | passed" in output
    assert "query_performance_baseline_evidence | no_tuning_applied_assertion | passed" in output

    assert "query_performance_tuning_status | passed" in output
    assert "query_performance_tuning_evidence | tuning_result_row_count_assertion | passed" in output
    assert "query_performance_tuning_evidence | tuning_index_created_assertion | passed" in output
    assert "query_performance_tuning_evidence | pre_post_report_ready_assertion | passed" in output

    assert "api_endpoint_baseline_status | passed" in output
    assert "api_endpoint_baseline_evidence | health_status_code_assertion | passed" in output
    assert "api_endpoint_baseline_evidence | review_list_status_code_assertion | passed" in output
    assert "api_endpoint_baseline_evidence | performance_metrics_captured_assertion | passed" in output

    assert "queue_performance_metrics_status | passed" in output
    assert "queue_performance_metrics_evidence | queue_total_count_assertion | passed" in output
    assert "queue_performance_metrics_evidence | queue_retry_pressure_assertion | passed" in output
    assert "queue_performance_metrics_evidence | queue_dead_letter_assertion | passed" in output
    assert "queue_performance_metrics_evidence | queue_history_metrics_assertion | passed" in output

    assert "overall_reliability_health_summary_status | passed" in output
    assert "RELIABILITY_HEALTH_SUMMARY_COMPLETE" in output