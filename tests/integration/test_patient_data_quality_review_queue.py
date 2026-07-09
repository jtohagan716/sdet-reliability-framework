import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
STALE_MESSAGE_SCHEMA = REPO_ROOT / "db" / "sql" / "010_fhir_stale_message_evidence.sql"
REVIEW_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "011_patient_data_quality_review_queue.sql"
VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "validate_patient_data_quality_review_queue.sql"


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
def test_patient_data_quality_review_queue_records_review_outcome():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    apply_schema(STALE_MESSAGE_SCHEMA)
    apply_schema(REVIEW_QUEUE_SCHEMA)

    result = run_validation_script()

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "Patient data quality review item:" in output
    assert "Patient data quality review action history:" in output
    assert "Protected current Encounter state remains unchanged:" in output
    assert "Original message history remains preserved:" in output

    assert "review_item_key" in output
    assert "dq-review-encounter-example-001-stale-message" in output

    assert "patient_reference" in output
    assert "Patient/example-patient-001" in output

    assert "encounter_reference" in output
    assert "Encounter/example-encounter-001" in output

    assert "review_priority" in output
    assert "medium" in output

    assert "review_status" in output
    assert "blessed_correct" in output

    assert "assigned_role" in output
    assert "Data Quality Expert" in output

    assert "reviewed_by" in output
    assert "synthetic_data_quality_reviewer" in output

    assert "review_outcome" in output
    assert "software_decision_correct" in output

    assert "action_type" in output
    assert "created" in output
    assert "blessed_correct" in output

    assert "current_sequence_number" in output
    assert "current_sequence_number      | 2" in output

    assert "current_resource_status" in output
    assert "current_resource_status      | finished" in output

    assert "current_payload_completeness" in output
    assert "current_payload_completeness | complete" in output

    assert "encounter-message-002-complete-review-queue" in output
    assert "encounter-message-001-partial-review-queue" in output

    assert "processing_status" in output
    assert "accepted" in output
    assert "stale" in output

    assert "review_item_assertion" in output
    assert "review_item_assertion | passed" in output

    assert "review_action_history_assertion" in output
    assert "review_action_history_assertion | passed" in output

    assert "protected_current_state_assertion" in output
    assert "protected_current_state_assertion | passed" in output

    assert "original_message_history_assertion" in output
    assert "original_message_history_assertion | passed" in output

    assert "ROLLBACK" in output