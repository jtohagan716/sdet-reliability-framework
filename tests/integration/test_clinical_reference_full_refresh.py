"""
Docker-backed validation for the clinical reference full refresh.

This test proves deterministic source-to-cache replacement, bidirectional
data reconciliation, synchronization evidence, and rollback isolation.
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
    / "validate_clinical_reference_full_refresh.sql"
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
def test_full_refresh_replaces_cache_reconciles_and_rolls_back():
    """Validate the successful full-refresh execution path."""

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
        "Clinical reference full-refresh validation failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    combined_output = result.stdout + result.stderr

    expected_assertions = [
        "full_refresh_row_count_assertion: passed",
        "stale_cache_replacement_assertion: passed",
        "cache_sync_metadata_assertion: passed",
        "bidirectional_data_reconciliation_assertion: passed",
        "sync_run_success_outcome_assertion: passed",
        "sync_table_result_success_outcome_assertion: passed",
    ]

    for expected_assertion in expected_assertions:
        assert expected_assertion in combined_output

    expected_codes = [
        "FOLLOWUP",
        "LEGACY",
        "ROUTINE",
        "TELEHEALTH",
        "URGENT",
    ]

    for expected_code in expected_codes:
        assert expected_code in combined_output

    assert "Obsolete Appointment" not in combined_output
    assert "completed" in combined_output
    assert "full_refresh" in combined_output
    assert "passed" in combined_output
    assert "ROLLBACK" in combined_output

    rollback_check = run_psql(
        """
        SELECT
            (
                SELECT COUNT(*)
                FROM sync_control.sync_run
                WHERE sync_run_id =
                    'dddddddd-dddd-dddd-dddd-dddddddddddd'
            ) AS remaining_sync_runs,
            (
                SELECT COUNT(*)
                FROM sync_control.sync_table_result
                WHERE sync_run_id =
                    'dddddddd-dddd-dddd-dddd-dddddddddddd'
            ) AS remaining_table_results,
            (
                SELECT COUNT(*)
                FROM facility_cache.appointment_type_reference
                WHERE sync_run_id =
                    'dddddddd-dddd-dddd-dddd-dddddddddddd'
            ) AS remaining_cache_records;
        """
    )

    assert rollback_check.returncode == 0, (
        "Full-refresh rollback verification failed.\n\n"
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