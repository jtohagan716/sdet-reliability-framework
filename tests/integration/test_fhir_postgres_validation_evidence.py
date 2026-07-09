import shutil
import subprocess
from pathlib import Path

import pytest


VALIDATION_SCRIPT = Path("scripts/validate_fhir_reference_validation_evidence.sql")


def docker_is_available() -> bool:
    """
    Return True when Docker is available to this test environment.
    """
    return shutil.which("docker") is not None


def postgres_service_is_available() -> bool:
    """
    Return True when the local Docker Compose PostgreSQL service is reachable.
    """
    command = [
        "docker",
        "compose",
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "sdet_user",
        "-d",
        "sdet_reliability",
        "-c",
        "SELECT 1;",
    ]

    result = subprocess.run(
        command,
        text=True,
        capture_output=True,
        timeout=15,
        check=False,
    )

    return result.returncode == 0


@pytest.mark.integration
def test_fhir_reference_validation_evidence_script_records_expected_finding():
    """
    Run the PostgreSQL FHIR validation evidence script and verify that it reports
    the expected negative reference finding.

    The script uses ROLLBACK, so this test proves the database evidence logic
    without leaving synthetic validation rows behind.
    """
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker Compose service is not available.")

    script_contents = VALIDATION_SCRIPT.read_text(encoding="utf-8")

    command = [
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
    ]

    result = subprocess.run(
        command,
        input=script_contents,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    output = result.stdout + result.stderr

    assert result.returncode == 0, output

    assert "FHIR validation run summary:" in output
    assert "FHIR resource check summary:" in output
    assert "FHIR reference check summary:" in output
    assert "Expected missing reference finding:" in output

    assert "DiagnosticReport/example-diagnosticreport-broken-001" in output
    assert "Observation/example-observation-missing-001" in output
    assert "check_status      | failed" in output or "check_status | failed" in output

    assert "ROLLBACK" in output