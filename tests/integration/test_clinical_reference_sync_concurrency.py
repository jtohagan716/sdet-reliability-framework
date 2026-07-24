"""
Validate same-domain clinical-reference synchronization locking.

The test holds the production advisory lock in one PostgreSQL session and
calls both synchronization modes from a second session. Each losing run must
fail cleanly without changing cache or checkpoint state.
"""

import subprocess
from pathlib import Path
from uuid import UUID

import psycopg
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_SCRIPT = (
    REPO_ROOT
    / "db"
    / "sql"
    / "013_clinical_reference_data_sync.sql"
)

DATABASE_DSN = (
    "postgresql://sdet_user:sdet_password"
    "@127.0.0.1:5432/sdet_reliability"
)

LOCK_ERROR_MESSAGE = (
    "Synchronization lock is already held for "
    "the appointment_type reference domain."
)

SCENARIOS = [
    (
        "full_refresh_appointment_type_reference",
        UUID("44444444-4444-4444-4444-444444444444"),
        "full_refresh",
    ),
    (
        "incremental_sync_appointment_type_reference",
        UUID("55555555-5555-5555-5555-555555555555"),
        "incremental",
    ),
]


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
    """Apply the repeatable clinical-reference schema."""

    assert SCHEMA_SCRIPT.exists(), (
        f"Schema script not found: {SCHEMA_SCRIPT}"
    )

    result = run_psql(
        SCHEMA_SCRIPT.read_text(encoding="utf-8")
    )

    assert result.returncode == 0, (
        "Clinical-reference schema application failed.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


def read_protected_state(
    connection: psycopg.Connection,
) -> tuple[list[tuple], list[tuple]]:
    """Read cache and checkpoint state protected by the domain lock."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                appointment_type_code,
                display_name,
                description,
                active_flag,
                effective_date,
                expiration_date,
                source_updated_at,
                source_version,
                sync_run_id,
                synced_at
            FROM facility_cache.appointment_type_reference
            ORDER BY appointment_type_code;
            """
        )
        cache_rows = cursor.fetchall()

        cursor.execute(
            """
            SELECT
                reference_domain,
                last_source_updated_at,
                last_source_key,
                last_successful_sync_run_id,
                updated_at
            FROM sync_control.sync_checkpoint
            ORDER BY reference_domain;
            """
        )
        checkpoint_rows = cursor.fetchall()

    return cache_rows, checkpoint_rows


def call_synchronization(
    connection: psycopg.Connection,
    procedure_name: str,
    sync_run_id: UUID,
) -> None:
    """Call a synchronization procedure with a five-second safety limit."""

    with connection.cursor() as cursor:
        # PostgreSQL interprets this integer value as milliseconds.
        cursor.execute(
            "SET LOCAL statement_timeout = 5000;"
        )

        cursor.execute(
            f"""
            CALL sync_control.{procedure_name} (
                %s,
                clock_timestamp(),
                clock_timestamp() + INTERVAL '5 minutes'
            );
            """,
            (sync_run_id,),
        )


def read_failure_evidence(
    connection: psycopg.Connection,
    sync_run_id: UUID,
) -> tuple[tuple | None, tuple | None]:
    """Read run-level and table-level synchronization evidence."""

    with connection.cursor() as cursor:
        cursor.execute(
            """
            SELECT
                reference_domain,
                load_mode,
                run_status,
                source_row_count,
                inserted_row_count,
                updated_row_count,
                target_row_count,
                reconciliation_status,
                error_message
            FROM sync_control.sync_run
            WHERE sync_run_id = %s;
            """,
            (sync_run_id,),
        )
        run_evidence = cursor.fetchone()

        cursor.execute(
            """
            SELECT
                source_table_name,
                target_table_name,
                table_status,
                source_row_count,
                inserted_row_count,
                updated_row_count,
                target_row_count,
                reconciliation_status,
                error_message
            FROM sync_control.sync_table_result
            WHERE sync_run_id = %s;
            """,
            (sync_run_id,),
        )
        table_evidence = cursor.fetchone()

    return run_evidence, table_evidence


@pytest.mark.integration
def test_same_domain_synchronization_runs_cannot_overlap():
    """Prove shared nonblocking locking for both synchronization modes."""

    postgres_available, availability_details = (
        postgres_service_is_available()
    )

    if not postgres_available:
        pytest.skip(
            "Docker Compose PostgreSQL service is unavailable: "
            f"{availability_details}"
        )

    apply_schema()

    lock_connection = None
    test_connection = None

    try:
        lock_connection = psycopg.connect(
            DATABASE_DSN,
            autocommit=False,
            connect_timeout=5,
        )
        test_connection = psycopg.connect(
            DATABASE_DSN,
            autocommit=False,
            connect_timeout=5,
        )

        with lock_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_try_advisory_xact_lock(
                    hashtext('sync_control.clinical_reference'),
                    hashtext('appointment_type')
                );
                """
            )
            lock_acquired = cursor.fetchone()[0]

        assert lock_acquired is True, (
            "The test could not acquire the controlling "
            "appointment_type advisory lock."
        )

        for procedure_name, sync_run_id, load_mode in SCENARIOS:
            state_before = read_protected_state(
                test_connection
            )
            expected_target_count = len(state_before[0])

            call_synchronization(
                test_connection,
                procedure_name,
                sync_run_id,
            )

            run_evidence, table_evidence = (
                read_failure_evidence(
                    test_connection,
                    sync_run_id,
                )
            )

            assert run_evidence == (
                "appointment_type",
                load_mode,
                "failed",
                0,
                0,
                0,
                expected_target_count,
                "failed",
                LOCK_ERROR_MESSAGE,
            )

            assert table_evidence == (
                "central_repository.appointment_type_reference",
                "facility_cache.appointment_type_reference",
                "failed",
                0,
                0,
                0,
                expected_target_count,
                "failed",
                LOCK_ERROR_MESSAGE,
            )

            state_after = read_protected_state(
                test_connection
            )

            assert state_after == state_before

            test_connection.rollback()

            with test_connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        (
                            SELECT COUNT(*)
                            FROM sync_control.sync_run
                            WHERE sync_run_id = %s
                        ),
                        (
                            SELECT COUNT(*)
                            FROM sync_control.sync_table_result
                            WHERE sync_run_id = %s
                        );
                        """,
                    (sync_run_id, sync_run_id),
                )
                remaining_evidence = cursor.fetchone()

            assert remaining_evidence == (0, 0)

            test_connection.rollback()

    except psycopg.OperationalError as error:
        pytest.fail(
            "Could not create the PostgreSQL sessions required "
            f"for concurrency validation: {error}"
        )

    finally:
        if test_connection is not None:
            test_connection.rollback()
            test_connection.close()

        if lock_connection is not None:
            lock_connection.rollback()
            lock_connection.close()
