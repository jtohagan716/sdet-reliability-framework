import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "011_patient_data_quality_review_queue.sql"
WORK_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "012_data_quality_work_queue.sql"
VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "validate_query_performance_baseline.sql"


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


@pytest.mark.integration
def test_query_performance_baseline_validation():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    apply_schema(REVIEW_QUEUE_SCHEMA)
    apply_schema(WORK_QUEUE_SCHEMA)

    result = run_validation_script()

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "Baseline query purpose: pending high-priority review items with related queue status." in output
    assert "Capturing EXPLAIN ANALYZE plan with buffers..." in output

    assert "QUERY PLAN | Sort" in output
    assert "Hash Right Join" in output
    assert "Seq Scan on public.data_quality_work_queue" in output
    assert "Seq Scan on public.patient_data_quality_review_items" in output
    assert "Buffers: shared hit=" in output
    assert "Planning Time:" in output
    assert "Execution Time:" in output

    assert "Running baseline query result check..." in output
    assert "review_item_key     | dq-perf-baseline-review-001" in output
    assert "review_item_key     | dq-perf-baseline-review-010" in output
    assert "queue_status        | ready" in output
    assert "queue_status        | processing" in output

    assert "baseline_row_count_assertion | passed" in output
    assert "queue_linkage_assertion | passed" in output
    assert "queue_status_distribution_assertion | passed" in output
    assert "no_tuning_applied_assertion | passed" in output

    assert "This script captures a baseline only. No indexes or configuration changes are applied." in output
    assert "ROLLBACK" in output