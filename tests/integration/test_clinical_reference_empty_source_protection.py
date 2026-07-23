"""
Docker-backed validation for empty-source cache protection.

This test proves that an unexpectedly empty central source does not erase
an existing facility cache and that the failed run is recorded accurately.
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
    / "validate_clinical_reference_empty_source_protection.sql"
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
def test_empty_source_preserves_cache_and_records_failure():
    """Validate the destructive-refresh safety guard."""

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
        "Empty-source protection validation failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    combined_output = result.stdout + result.stderr

    expected_assertions = [
        "empty_source_precondition_assertion: passed",
        "existing_cache_preservation_assertion: passed",
        "empty_source_run_failure_assertion: passed",
        "empty_source_table_failure_assertion: passed",
    ]

    for expected_assertion in expected_assertions:
        assert expected_assertion in combined_output

    assert "ROUTINE" in combined_output
    assert "Routine Visit" in combined_output
    assert "failed" in combined_output

    assert (
        "Source table is empty; full refresh aborted "
        "to protect the facility cache."
        in combined_output
    )

    assert (
        "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
        in combined_output
    )

    assert (
        "ffffffff-ffff-ffff-ffff-ffffffffffff"
        in combined_output
    )

    assert "ROLLBACK" in combined_output

    rollback_check = run_psql(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM sync_control.sync_run
                WHERE sync_run_id IN (
                    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
                    'ffffffff-ffff-ffff-ffff-ffffffffffff'
                )
            ) AS remaining_sync_runs,
            (
                SELECT COUNT(*)
                FROM sync_control.sync_table_result
                WHERE sync_run_id IN (
                    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
                    'ffffffff-ffff-ffff-ffff-ffffffffffff'
                )
            ) AS remaining_table_results,
            (
                SELECT COUNT(*)
                FROM facility_cache.appointment_type_reference
                WHERE sync_run_id IN (
                    'eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee',
                    'ffffffff-ffff-ffff-ffff-ffffffffffff'
                )
            ) AS remaining_cache_records;
        """
    )

    assert rollback_check.returncode == 0, (
        "Empty-source rollback verification failed.\n\n"
        f"STDOUT:\n{rollback_check.stdout}\n\n"
        f"STDERR:\n{rollback_check.stderr}"
    )

    data_lines = [
        line.strip()
        for line in rollback_check.stdout.splitlines()
        if "|" in line
    ]

    assert any(
        line.replace(" ", "") == "0|0|0"
        for line in data_lines
    ), rollback_check.stdout