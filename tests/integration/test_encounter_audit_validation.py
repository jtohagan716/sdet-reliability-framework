"""
Integration test for PostgreSQL encounter audit validation.

This test runs the SQL validation script against the local Docker Compose
PostgreSQL service and verifies that the encounter audit trigger records the
expected INSERT and UPDATE audit rows.

Prerequisite:
    docker compose up -d
"""

import subprocess
from pathlib import Path

import pytest


PROJECT_ROOT = Path(__file__).resolve().parents[2]
VALIDATION_SCRIPT = PROJECT_ROOT / "scripts" / "validate_encounter_audit.sql"


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

    sql_text = VALIDATION_SCRIPT.read_text(encoding="utf-8")

    try:
        result = run_psql_script(sql_text)
    except FileNotFoundError:
        pytest.skip("Docker is not available in this environment.")

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