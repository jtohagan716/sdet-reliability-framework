import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "011_patient_data_quality_review_queue.sql"
WORK_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "012_data_quality_work_queue.sql"
VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "validate_query_performance_tuning_comparison.sql"


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
def test_query_performance_tuning_comparison_validation():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    apply_schema(REVIEW_QUEUE_SCHEMA)
    apply_schema(WORK_QUEUE_SCHEMA)

    result = run_validation_script()

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "Creating larger synthetic patient data quality review dataset for pre/post tuning comparison..." in output
    assert "INSERT 0 10000" in output
    assert "Creating matching queue records for performance tuning comparison dataset..." in output

    assert "Pre-tuning dataset summary:" in output
    assert "total_review_items  | 10000" in output
    assert "target_review_items | 100" in output
    assert "total_queue_items      | 10000" in output
    assert "ready_queue_items      | 80" in output
    assert "processing_queue_items | 20" in output
    assert "completed_queue_items  | 9900" in output

    assert "PRE-TUNING PLAN: pending high-priority review items with related queue status." in output
    assert "POST-TUNING PLAN: same query after targeted composite index." in output

    assert "Planning Time:" in output
    assert "Execution Time:" in output
    assert "Buffers: shared hit=" in output

    assert "Bitmap Heap Scan on public.patient_data_quality_review_items" in output
    assert "BitmapAnd" in output
    assert "idx_patient_data_quality_review_items_review_priority" in output
    assert "idx_patient_data_quality_review_items_review_status" in output

    assert "Applying one targeted tuning change: composite index" in output
    assert "CREATE INDEX" in output
    assert "idx_perf_tuning_review_status_priority_created_key" in output
    assert "Index Scan using idx_perf_tuning_review_status_priority_created_key" in output

    assert "Running tuned query result check..." in output
    assert "review_item_key     | dq-perf-tuning-review-00001" in output
    assert "review_item_key     | dq-perf-tuning-review-00025" in output
    assert "queue_status        | ready" in output

    assert "tuning_result_row_count_assertion | passed" in output
    assert "tuning_target_dataset_assertion | passed" in output
    assert "tuning_queue_linkage_assertion | passed" in output
    assert "tuning_index_created_assertion | passed" in output
    assert "pre_post_report_ready_assertion | passed" in output

    assert (
        "This script captures pre/post query plans and applies one targeted composite index "
        "inside a rollback-safe transaction."
    ) in output

    assert "ROLLBACK" in output