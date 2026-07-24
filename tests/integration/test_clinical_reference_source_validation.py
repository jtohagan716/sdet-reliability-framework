"""
Docker-backed integration validation for the clinical reference source schema.

The test applies the PostgreSQL schema, runs controlled source-data validation,
and verifies that valid records are accepted while invalid records are rejected.
The validation transaction is rolled back so repeated runs begin cleanly.
"""

import subprocess
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_SCRIPT = (
    REPO_ROOT
    / "db"
    / "sql"
    / "013_clinical_reference_data_sync.sql"
)

VALIDATION_SCRIPT = (
    REPO_ROOT
    / "scripts"
    / "validate_clinical_reference_source.sql"
)


def postgres_service_is_available() -> tuple[bool, str]:
    """Return whether the Docker Compose PostgreSQL service is ready."""

    command = [
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
    ]

    try:
        result = subprocess.run(
            command,
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return False, "Docker is not installed or is not on PATH."

    if result.returncode != 0:
        details = (
            result.stderr
            or result.stdout
            or "PostgreSQL service is not ready."
        ).strip()

        return False, details

    return True, result.stdout.strip()


def run_psql(sql_text: str) -> subprocess.CompletedProcess[str]:
    """Execute SQL through the repository Docker Compose PostgreSQL service."""

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
        "-v",
        "ON_ERROR_STOP=1",
    ]

    return subprocess.run(
        command,
        cwd=REPO_ROOT,
        input=sql_text,
        capture_output=True,
        text=True,
        check=False,
    )


def apply_schema() -> None:
    """Apply the repeatable clinical reference-data schema."""

    assert SCHEMA_SCRIPT.exists(), (
        f"Schema script not found: {SCHEMA_SCRIPT}"
    )

    result = run_psql(
        SCHEMA_SCRIPT.read_text(encoding="utf-8")
    )

    assert result.returncode == 0, (
        "Clinical reference schema failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


@pytest.mark.integration
def test_clinical_reference_source_constraints_and_rollback():
    """Validate source constraints and reproducible rollback behavior."""

    assert VALIDATION_SCRIPT.exists(), (
        f"Validation script not found: {VALIDATION_SCRIPT}"
    )

    postgres_available, availability_details = (
        postgres_service_is_available()
    )

    if not postgres_available:
        pytest.skip(
            "Docker Compose PostgreSQL service is unavailable: "
            f"{availability_details}"
        )

    apply_schema()

    result = run_psql(
        VALIDATION_SCRIPT.read_text(encoding="utf-8")
    )

    assert result.returncode == 0, (
        "Clinical reference source validation failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    combined_output = result.stdout + result.stderr

    assert "ROUTINE" in combined_output
    assert "Routine Visit" in combined_output

    assert (
        "blank_code_constraint_assertion: passed"
        in combined_output
    )

    assert (
        "blank_display_name_constraint_assertion: passed"
        in combined_output
    )

    assert (
        "date_range_constraint_assertion: passed"
        in combined_output
    )

    assert (
        "source_version_constraint_assertion: passed"
        in combined_output
    )

    assert (
        "duplicate_business_key_assertion: passed"
        in combined_output
    )

    assert "valid_test_record_count" in combined_output
    assert "ROLLBACK" in combined_output

    rollback_check = run_psql(
        """
        SELECT COUNT(*)
        FROM central_repository.appointment_type_reference
        WHERE appointment_type_code = 'ROUTINE';
        """
    )

    assert rollback_check.returncode == 0, rollback_check.stderr
    assert rollback_check.stdout.strip().endswith("(1 row)")

    output_lines = [
        line.strip()
        for line in rollback_check.stdout.splitlines()
    ]

    assert "0" in output_lines