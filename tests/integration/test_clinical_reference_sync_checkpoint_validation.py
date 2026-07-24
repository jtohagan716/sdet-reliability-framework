"""
Docker-backed validation for synchronization checkpoints.

This test verifies checkpoint uniqueness, required values, synchronization-run
referential integrity, and rollback isolation.
"""

import re
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
    / "validate_clinical_reference_sync_checkpoint.sql"
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
    """Execute SQL through the repository PostgreSQL service."""

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
    """Apply the repeatable clinical reference synchronization schema."""

    assert SCHEMA_SCRIPT.exists(), (
        f"Schema script not found: {SCHEMA_SCRIPT}"
    )

    result = run_psql(
        SCHEMA_SCRIPT.read_text(encoding="utf-8")
    )

    assert result.returncode == 0, (
        "Clinical reference synchronization schema failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


@pytest.mark.integration
def test_sync_checkpoint_constraints_and_rollback():
    """Validate checkpoint integrity and rollback behavior."""

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
        "Synchronization checkpoint validation failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    combined_output = result.stdout + result.stderr

    expected_assertions = [
        "checkpoint_domain_uniqueness_assertion: passed",
        "checkpoint_domain_not_blank_assertion: passed",
        "checkpoint_source_key_not_blank_assertion: passed",
        "checkpoint_sync_run_foreign_key_assertion: passed",
    ]

    for expected_assertion in expected_assertions:
        assert expected_assertion in combined_output

    assert "appointment_type" in combined_output
    assert "URGENT" in combined_output

    assert (
        "12121212-1212-1212-1212-121212121212"
        in combined_output
    )

    assert "ROLLBACK" in combined_output

    count_pattern = re.compile(
        r"valid_checkpoint_count"
        r"\s*-+\s*"
        r"1\s*"
        r"\(1 row\)",
        re.DOTALL,
    )

    assert count_pattern.search(combined_output), (
        "Expected exactly one valid synchronization checkpoint.\n\n"
        f"OUTPUT:\n{combined_output}"
    )

    rollback_check = run_psql(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM sync_control.sync_checkpoint
                WHERE reference_domain = 'appointment_type'
            ) AS remaining_checkpoints,
            (
                SELECT COUNT(*)
                FROM sync_control.sync_run
                WHERE sync_run_id =
                    '12121212-1212-1212-1212-121212121212'
            ) AS remaining_sync_runs;
        """
    )

    assert rollback_check.returncode == 0, (
        "Checkpoint rollback verification failed.\n\n"
        f"STDOUT:\n{rollback_check.stdout}\n\n"
        f"STDERR:\n{rollback_check.stderr}"
    )

    data_lines = [
        line.strip()
        for line in rollback_check.stdout.splitlines()
        if "|" in line
    ]

    assert any(
        line.replace(" ", "") == "0|0"
        for line in data_lines
    ), rollback_check.stdout