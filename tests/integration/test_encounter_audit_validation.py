"""
Integration test for PostgreSQL encounter audit validation.

This test runs the SQL validation script against the local Docker Compose
PostgreSQL service and verifies that the encounter audit trigger records the
expected INSERT and UPDATE audit rows.

This is a Docker-backed integration test. It runs when the local PostgreSQL
Compose service is available and skips cleanly when that service is not running,
such as in a default GitHub Actions unit-test job.
"""

import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_SCRIPT = PROJECT_ROOT / "scripts" / "validate_encounter_audit.sql"


def postgres_compose_service_is_available() -> tuple[bool, str]:
    """
    Return whether the Docker Compose PostgreSQL service is available.

    This prevents the integration test from failing in environments where the
    Docker Compose stack has not been started, such as a generic CI pytest job.
    """

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
            text=True,
            capture_output=True,
            cwd=PROJECT_ROOT,
            check=False,
        )
    except FileNotFoundError:
        return False, "Docker is not available."

    if result.returncode != 0:
        details = (result.stderr or result.stdout or "PostgreSQL service is not ready.").strip()
        return False, details

    return True, result.stdout.strip()


def run_psql_script(sql_text: str) -> subprocess.CompletedProcess:
    """
    Run SQL against the Docker Compose PostgreSQL service using psql.

    This intentionally validates the same path a developer would use locally:
    Docker Compose -> PostgreSQL -> audit trigger -> validation query.
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
        "-v",
        "ON_ERROR_STOP=1",
    ]

    return subprocess.run(
        command,
        input=sql_text,
        text=True,
        capture_output=True,
        cwd=PROJECT_ROOT,
        check=False,
    )


def extract_audit_result_rows(psql_output: str) -> list[str]:
    """
    Extract only the audit result rows from psql output.

    This avoids accidentally counting command messages such as:
        INSERT 0 1
        UPDATE 1
    """

    return [
        line.strip()
        for line in psql_output.splitlines()
        if "|" in line and "audit_validation_test" in line
    ]


@pytest.mark.integration
def test_encounter_audit_validation_script_records_insert_and_update():
    """
    Validate that the PostgreSQL encounter audit trigger captures:

    - one INSERT audit row
    - one UPDATE audit row
    - old/new status values
    - audit metadata from SET LOCAL
    - transaction rollback behavior from the validation script
    """

    if not VALIDATION_SCRIPT.exists():
        pytest.fail(f"Validation script not found: {VALIDATION_SCRIPT}")

    postgres_available, availability_message = postgres_compose_service_is_available()

    if not postgres_available:
        pytest.skip(
            "Docker Compose PostgreSQL service is not available for this "
            f"integration test: {availability_message}"
        )

    sql_text = VALIDATION_SCRIPT.read_text(encoding="utf-8")
    result = run_psql_script(sql_text)

    if result.returncode != 0:
        pytest.fail(
            "Audit validation SQL failed.\n\n"
            f"STDOUT:\n{result.stdout}\n\n"
            f"STDERR:\n{result.stderr}"
        )

    output = result.stdout
    audit_rows = extract_audit_result_rows(output)

    assert len(audit_rows) == 2, output

    insert_row = audit_rows[0]
    update_row = audit_rows[1]

    assert "| INSERT" in insert_row
    assert "| scheduled" in insert_row
    assert "| audit_validation_test" in insert_row
    assert "| manual_sql_validation" in insert_row

    assert "| UPDATE" in update_row
    assert "| scheduled" in update_row
    assert "| completed" in update_row
    assert "| audit_validation_test" in update_row
    assert "| manual_sql_validation" in update_row

    assert "(2 rows)" in output
    assert "ROLLBACK" in output