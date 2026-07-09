import shutil
import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_SCRIPT = REPO_ROOT / "scripts" / "validate_fhir_stale_message_evidence.sql"


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


def run_validation_script() -> subprocess.CompletedProcess[str]:
    script_contents = VALIDATION_SCRIPT.read_text(encoding="utf-8")

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


@pytest.mark.integration
def test_fhir_stale_message_postgres_evidence_records_archive_and_protected_state():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not VALIDATION_SCRIPT.exists():
        pytest.fail(f"Validation script not found: {VALIDATION_SCRIPT}")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    result = run_validation_script()

    assert result.returncode == 0, result.stderr

    output = result.stdout

    assert "FHIR stale-message event history:" in output
    assert "Protected current Encounter state:" in output
    assert "Archived stale-message decision:" in output
    assert "Expected protected state assertion:" in output
    assert "Expected stale archive assertion:" in output
    assert "Expected append-only history assertion:" in output

    assert "event_id             | encounter-message-002-complete" in output
    assert "event_id             | encounter-message-001-partial" in output

    assert "current_sequence_number      | 2" in output
    assert "current_resource_status      | finished" in output
    assert "current_payload_completeness | complete" in output
    assert "source_event_id              | encounter-message-002-complete" in output

    assert "stale_event_id               | encounter-message-001-partial" in output
    assert "stale_sequence_number        | 1" in output
    assert "decision_status              | stale_archived" in output

    assert (
        "risk_prevented               | Prevented downgrade from finished complete state "
        "to in-progress partial state"
    ) in output

    assert "protected_state_assertion" in output
    assert "protected_state_assertion | passed" in output

    assert "stale_archive_assertion" in output
    assert "stale_archive_assertion | passed" in output

    assert "append_only_history_assertion" in output
    assert "append_only_history_assertion | passed" in output

    assert "ROLLBACK" in output