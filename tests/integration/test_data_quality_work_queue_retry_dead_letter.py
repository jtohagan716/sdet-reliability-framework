import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
REVIEW_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "011_patient_data_quality_review_queue.sql"
WORK_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "012_data_quality_work_queue.sql"
VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "validate_data_quality_work_queue_retry_dead_letter.sql"


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
def test_data_quality_work_queue_retries_and_moves_to_dead_letter():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    apply_schema(REVIEW_QUEUE_SCHEMA)
    apply_schema(WORK_QUEUE_SCHEMA)

    result = run_validation_script()

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "Enqueuing work item with max_attempts set to 2..." in output
    assert "Worker attempts first claim..." in output
    assert "Simulating first worker failure..." in output
    assert "Scheduling retry because attempt_count is below max_attempts..." in output
    assert "Worker attempts second claim..." in output
    assert "Simulating second worker failure at max attempts..." in output
    assert "Moving work item to dead_letter after max attempts reached..." in output

    assert "work_item_key          | dq-work-queue-retry-dead-letter-001" in output
    assert "queue_name             | patient_data_quality_review" in output
    assert "event_type             | patient_data_quality_review_created" in output
    assert "source_review_item_key | dq-review-retry-dead-letter-encounter-example-001" in output
    assert "patient_reference      | Patient/example-patient-001" in output
    assert "encounter_reference    | Encounter/example-encounter-retry-dead-letter-001" in output
    assert "priority               | high" in output
    assert "status                 | dead_letter" in output
    assert "attempt_count          | 2" in output
    assert "max_attempts           | 2" in output
    assert "processed_at_recorded  | t" in output
    assert (
        "error_message          | Simulated persistent reconciliation preparation failure "
        "after max attempts"
    ) in output

    assert "action_type     | created" in output
    assert "action_type     | claimed" in output
    assert "action_type     | failed" in output
    assert "action_type     | retry_scheduled" in output
    assert "action_type     | moved_to_dead_letter" in output

    assert "action_by       | synthetic_queue_worker_retry_001" in output
    assert "action_by       | synthetic_queue_worker_retry_002" in output
    assert "action_by       | queue_retry_policy" in output

    assert "review_item_key     | dq-review-retry-dead-letter-encounter-example-001" in output
    assert "review_priority     | high" in output
    assert "review_status       | pending_review" in output
    assert "assigned_role       | Data Quality Expert" in output

    assert "retry_attempt_assertion | passed" in output
    assert "dead_letter_assertion | passed" in output
    assert "retry_history_assertion | passed" in output
    assert "review_item_unchanged_assertion | passed" in output
    assert "queue_linkage_assertion | passed" in output

    assert "ROLLBACK" in output