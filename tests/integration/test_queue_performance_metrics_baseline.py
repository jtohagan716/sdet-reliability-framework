import re
import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "011_patient_data_quality_review_queue.sql"
WORK_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "012_data_quality_work_queue.sql"
VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "validate_queue_performance_metrics_baseline.sql"


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


def run_sql(script_contents: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-x",
            "-v",
            "ON_ERROR_STOP=1",
            "-U",
            "sdet_user",
            "-d",
            "sdet_reliability",
        ],
        cwd=REPO_ROOT,
        input=script_contents,
        capture_output=True,
        text=True,
        check=False,
    )


def apply_schema(schema_path: Path) -> None:
    assert schema_path.exists(), f"Schema not found: {schema_path}"

    result = run_sql(schema_path.read_text(encoding="utf-8"))

    assert result.returncode == 0, result.stderr


def run_validation_script() -> subprocess.CompletedProcess[str]:
    assert VALIDATION_SCRIPT.exists(), f"Validation script not found: {VALIDATION_SCRIPT}"

    return run_sql(VALIDATION_SCRIPT.read_text(encoding="utf-8"))


def assert_metric(output: str, metric_name: str, expected_value: str) -> None:
    pattern = rf"{re.escape(metric_name)}\s+\|\s+{re.escape(expected_value)}"
    assert re.search(pattern, output), f"Expected metric not found: {metric_name} | {expected_value}"


@pytest.mark.integration
def test_queue_performance_metrics_baseline_validation():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    apply_schema(REVIEW_QUEUE_SCHEMA)
    apply_schema(WORK_QUEUE_SCHEMA)

    result = run_validation_script()

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "QUEUE_PERFORMANCE_METRICS_BASELINE_START" in output
    assert "Creating synthetic patient data quality review records for queue metrics baseline..." in output
    assert "Creating synthetic work queue records with deterministic status distribution..." in output
    assert "Creating synthetic queue history records for metrics baseline..." in output

    assert "Queue status distribution metrics:" in output
    assert_metric(output, "queue_total_count", "30")
    assert_metric(output, "queue_ready_count", "10")
    assert_metric(output, "queue_processing_count", "5")
    assert_metric(output, "queue_completed_count", "7")
    assert_metric(output, "queue_failed_count", "4")
    assert_metric(output, "queue_dead_letter_count", "4")

    assert "Queue retry and attempt metrics:" in output
    assert_metric(output, "queue_retry_eligible_count", "4")
    assert_metric(output, "queue_max_attempt_count", "3")
    assert "queue_average_attempt_count" in output

    assert "Queue backlog age metrics:" in output
    assert "oldest_ready_item_age_minutes" in output
    assert "oldest_processing_item_age_minutes" in output
    assert "queue_age_under_15_min_count" in output
    assert "queue_age_15_to_45_min_count" in output
    assert "queue_age_over_45_min_count" in output

    assert "Queue history action metrics:" in output
    assert_metric(output, "history_created_count", "30")
    assert_metric(output, "history_claimed_count", "20")
    assert_metric(output, "history_completed_count", "7")
    assert_metric(output, "history_failed_count", "8")
    assert_metric(output, "history_retry_scheduled_count", "4")
    assert_metric(output, "history_moved_to_dead_letter_count", "4")

    assert "queue_total_count_assertion | passed" in output
    assert "queue_status_distribution_assertion | passed" in output
    assert "queue_retry_pressure_assertion | passed" in output
    assert "queue_dead_letter_assertion | passed" in output
    assert "queue_age_metrics_assertion | passed" in output
    assert "queue_processing_age_metrics_assertion | passed" in output
    assert "queue_history_metrics_assertion | passed" in output

    assert "This script captures queue health metrics only. It does not run a throughput or load test." in output
    assert "ROLLBACK" in output