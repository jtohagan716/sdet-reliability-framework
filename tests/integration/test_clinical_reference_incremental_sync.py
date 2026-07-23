"""
Docker-backed validation for successful incremental synchronization.

This test proves that the incremental procedure inserts new cache rows,
updates existing cache rows, preserves rows at or before the checkpoint,
records accurate evidence, advances the checkpoint, and rolls back cleanly.
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
    / "validate_clinical_reference_incremental_sync.sql"
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
    """Apply the repeatable clinical synchronization schema."""

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
def test_incremental_sync_inserts_updates_and_advances_checkpoint():
    """Validate the successful incremental synchronization path."""

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
        "Incremental synchronization validation failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )

    combined_output = result.stdout + result.stderr

    expected_assertions = [
        "incremental_target_count_assertion: passed",
        "incremental_insert_assertion: passed",
        "incremental_update_assertion: passed",
        "incremental_unchanged_rows_assertion: passed",
        "incremental_checkpoint_advancement_assertion: passed",
        "incremental_run_evidence_assertion: passed",
        "incremental_table_evidence_assertion: passed",
    ]

    for expected_assertion in expected_assertions:
        assert expected_assertion in combined_output

    assert "Post-treatment Follow-up" in combined_output
    assert "URGENT" in combined_output
    assert "FOLLOWUP" in combined_output
    assert "incremental" in combined_output
    assert "completed" in combined_output
    assert "passed" in combined_output

    assert (
        "33333333-3333-3333-3333-333333333333"
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
                    '22222222-2222-2222-2222-222222222222',
                    '33333333-3333-3333-3333-333333333333'
                )
            ) AS remaining_sync_runs,
            (
                SELECT COUNT(*)
                FROM sync_control.sync_table_result
                WHERE sync_run_id IN (
                    '22222222-2222-2222-2222-222222222222',
                    '33333333-3333-3333-3333-333333333333'
                )
            ) AS remaining_table_results,
            (
                SELECT COUNT(*)
                FROM facility_cache.appointment_type_reference
                WHERE sync_run_id IN (
                    '22222222-2222-2222-2222-222222222222',
                    '33333333-3333-3333-3333-333333333333'
                )
            ) AS remaining_cache_rows,
            (
                SELECT COUNT(*)
                FROM sync_control.sync_checkpoint
                WHERE last_successful_sync_run_id IN (
                    '22222222-2222-2222-2222-222222222222',
                    '33333333-3333-3333-3333-333333333333'
                )
            ) AS remaining_checkpoints;
        """
    )

    assert rollback_check.returncode == 0, (
        "Incremental synchronization rollback verification failed.\n\n"
        f"STDOUT:\n{rollback_check.stdout}\n\n"
        f"STDERR:\n{rollback_check.stderr}"
    )

    data_lines = [
        line.strip()
        for line in rollback_check.stdout.splitlines()
        if "|" in line
    ]

    assert any(
        line.replace(" ", "") == "0|0|0|0"
        for line in data_lines
    ), rollback_check.stdout