"""
Validate deterministic recovery after a failed incremental synchronization.

A temporary database is created for the test. The first incremental attempt
loses the domain lock and fails without changing cache or checkpoint state.
After the lock is released, a second attempt processes the same source change
exactly once and advances the checkpoint.
"""

import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import UUID

import psycopg
from psycopg import sql
import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]

SCHEMA_SCRIPT = (
    REPO_ROOT
    / "db"
    / "sql"
    / "013_clinical_reference_data_sync.sql"
)

TEMP_DATABASE = "sdet_clinical_retry_validation"

MAINTENANCE_DSN = (
    "postgresql://sdet_user:sdet_password"
    "@127.0.0.1:5432/postgres"
)

TEST_DATABASE_DSN = (
    "postgresql://sdet_user:sdet_password"
    f"@127.0.0.1:5432/{TEMP_DATABASE}"
)

BASELINE_RUN_ID = UUID(
    "66666666-6666-6666-6666-666666666666"
)

FAILED_RUN_ID = UUID(
    "77777777-7777-7777-7777-777777777777"
)

RETRY_RUN_ID = UUID(
    "88888888-8888-8888-8888-888888888888"
)

BASELINE_CODE = "RETRY_BASELINE"
RETRY_CODE = "RETRY_RECOVERY"

BASELINE_UPDATED_AT = datetime(
    2026,
    1,
    1,
    tzinfo=timezone.utc,
)

RETRY_UPDATED_AT = datetime(
    2026,
    1,
    2,
    tzinfo=timezone.utc,
)

LOCK_ERROR_MESSAGE = (
    "Synchronization lock is already held for "
    "the appointment_type reference domain."
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


def run_psql(
    sql_text: str,
    database_name: str,
) -> subprocess.CompletedProcess[str]:
    """Execute SQL through the Docker Compose PostgreSQL service."""

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
        database_name,
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


def recreate_temp_database() -> None:
    """Create a clean database used only by this validation."""

    with psycopg.connect(
        MAINTENANCE_DSN,
        autocommit=True,
        connect_timeout=5,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s
                  AND pid <> pg_backend_pid();
                """,
                (TEMP_DATABASE,),
            )

            cursor.execute(
                sql.SQL(
                    "DROP DATABASE IF EXISTS {}"
                ).format(
                    sql.Identifier(TEMP_DATABASE)
                )
            )

            cursor.execute(
                sql.SQL(
                    "CREATE DATABASE {}"
                ).format(
                    sql.Identifier(TEMP_DATABASE)
                )
            )


def drop_temp_database() -> None:
    """Remove the temporary validation database."""

    with psycopg.connect(
        MAINTENANCE_DSN,
        autocommit=True,
        connect_timeout=5,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT pg_terminate_backend(pid)
                FROM pg_stat_activity
                WHERE datname = %s
                  AND pid <> pg_backend_pid();
                """,
                (TEMP_DATABASE,),
            )

            cursor.execute(
                sql.SQL(
                    "DROP DATABASE IF EXISTS {}"
                ).format(
                    sql.Identifier(TEMP_DATABASE)
                )
            )


def apply_schema() -> None:
    """Apply the complete schema to the new temporary database."""

    assert SCHEMA_SCRIPT.exists(), (
        f"Schema script not found: {SCHEMA_SCRIPT}"
    )

    result = run_psql(
        SCHEMA_SCRIPT.read_text(encoding="utf-8"),
        TEMP_DATABASE,
    )

    assert result.returncode == 0, (
        "Clinical-reference schema failed in the temporary database.\n\n"
        f"STDOUT:\n{result.stdout}\n\n"
        f"STDERR:\n{result.stderr}"
    )


def establish_baseline() -> None:
    """Create one source row and a successful full-refresh checkpoint."""

    with psycopg.connect(
        TEST_DATABASE_DSN,
        autocommit=False,
        connect_timeout=5,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO
                    central_repository.appointment_type_reference (
                        appointment_type_code,
                        display_name,
                        description,
                        active_flag,
                        effective_date,
                        expiration_date,
                        source_updated_at,
                        source_version
                    )
                VALUES (
                    %s,
                    'Retry Baseline',
                    'Baseline row for retry validation.',
                    TRUE,
                    DATE '2026-01-01',
                    NULL,
                    %s,
                    1
                );
                """,
                (
                    BASELINE_CODE,
                    BASELINE_UPDATED_AT,
                ),
            )

            cursor.execute(
                """
                CALL
                    sync_control.full_refresh_appointment_type_reference (
                        %s,
                        clock_timestamp(),
                        clock_timestamp() + INTERVAL '5 minutes'
                    );
                """,
                (BASELINE_RUN_ID,),
            )

            cursor.execute(
                """
                SELECT
                    run_status,
                    reconciliation_status
                FROM sync_control.sync_run
                WHERE sync_run_id = %s;
                """,
                (BASELINE_RUN_ID,),
            )

            assert cursor.fetchone() == (
                "completed",
                "passed",
            )

            cursor.execute(
                """
                SELECT
                    last_source_updated_at,
                    last_source_key,
                    last_successful_sync_run_id
                FROM sync_control.sync_checkpoint
                WHERE reference_domain = 'appointment_type';
                """
            )

            assert cursor.fetchone() == (
                BASELINE_UPDATED_AT,
                BASELINE_CODE,
                BASELINE_RUN_ID,
            )

        connection.commit()


def call_incremental_sync(
    connection: psycopg.Connection,
    sync_run_id: UUID,
) -> None:
    """Call incremental synchronization with a bounded timeout."""

    with connection.cursor() as cursor:
        cursor.execute(
            "SET LOCAL statement_timeout = 5000;"
        )

        cursor.execute(
            """
            CALL
                sync_control.incremental_sync_appointment_type_reference (
                    %s,
                    clock_timestamp(),
                    clock_timestamp() + INTERVAL '5 minutes'
                );
            """,
            (sync_run_id,),
        )


@pytest.mark.integration
def test_failed_incremental_attempt_can_be_retried_exactly_once():
    """Prove failure safety and deterministic retry recovery."""

    postgres_available, availability_details = (
        postgres_service_is_available()
    )

    if not postgres_available:
        pytest.skip(
            "Docker Compose PostgreSQL service is unavailable: "
            f"{availability_details}"
        )

    database_created = False
    lock_connection = None
    test_connection = None

    try:
        recreate_temp_database()
        database_created = True

        apply_schema()
        establish_baseline()

        lock_connection = psycopg.connect(
            TEST_DATABASE_DSN,
            autocommit=False,
            connect_timeout=5,
        )

        test_connection = psycopg.connect(
            TEST_DATABASE_DSN,
            autocommit=False,
            connect_timeout=5,
        )

        with test_connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO
                    central_repository.appointment_type_reference (
                        appointment_type_code,
                        display_name,
                        description,
                        active_flag,
                        effective_date,
                        expiration_date,
                        source_updated_at,
                        source_version
                    )
                VALUES (
                    %s,
                    'Retry Recovery Validation',
                    'Source row processed after a controlled failure.',
                    TRUE,
                    DATE '2026-01-02',
                    NULL,
                    %s,
                    2
                );
                """,
                (
                    RETRY_CODE,
                    RETRY_UPDATED_AT,
                ),
            )

            cursor.execute(
                """
                SELECT
                    last_source_updated_at,
                    last_source_key,
                    last_successful_sync_run_id
                FROM sync_control.sync_checkpoint
                WHERE reference_domain = 'appointment_type';
                """
            )
            checkpoint_before = cursor.fetchone()

        assert checkpoint_before == (
            BASELINE_UPDATED_AT,
            BASELINE_CODE,
            BASELINE_RUN_ID,
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

            assert cursor.fetchone()[0] is True

        call_incremental_sync(
            test_connection,
            FAILED_RUN_ID,
        )

        with test_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
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
                (FAILED_RUN_ID,),
            )

            assert cursor.fetchone() == (
                "incremental",
                "failed",
                0,
                0,
                0,
                1,
                "failed",
                LOCK_ERROR_MESSAGE,
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM facility_cache.appointment_type_reference
                WHERE appointment_type_code = %s;
                """,
                (RETRY_CODE,),
            )

            assert cursor.fetchone()[0] == 0

            cursor.execute(
                """
                SELECT
                    last_source_updated_at,
                    last_source_key,
                    last_successful_sync_run_id
                FROM sync_control.sync_checkpoint
                WHERE reference_domain = 'appointment_type';
                """
            )

            assert cursor.fetchone() == checkpoint_before

        lock_connection.rollback()

        call_incremental_sync(
            test_connection,
            RETRY_RUN_ID,
        )

        with test_connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
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
                (RETRY_RUN_ID,),
            )

            assert cursor.fetchone() == (
                "incremental",
                "completed",
                1,
                1,
                0,
                2,
                "passed",
                None,
            )

            cursor.execute(
                """
                SELECT
                    appointment_type_code,
                    display_name,
                    source_updated_at,
                    source_version,
                    sync_run_id
                FROM facility_cache.appointment_type_reference
                WHERE appointment_type_code = %s;
                """,
                (RETRY_CODE,),
            )

            assert cursor.fetchone() == (
                RETRY_CODE,
                "Retry Recovery Validation",
                RETRY_UPDATED_AT,
                2,
                RETRY_RUN_ID,
            )

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM facility_cache.appointment_type_reference
                WHERE appointment_type_code = %s;
                """,
                (RETRY_CODE,),
            )

            assert cursor.fetchone()[0] == 1

            cursor.execute(
                """
                SELECT
                    last_source_updated_at,
                    last_source_key,
                    last_successful_sync_run_id
                FROM sync_control.sync_checkpoint
                WHERE reference_domain = 'appointment_type';
                """
            )

            assert cursor.fetchone() == (
                RETRY_UPDATED_AT,
                RETRY_CODE,
                RETRY_RUN_ID,
            )

            cursor.execute(
                """
                SELECT
                    run_status,
                    error_message
                FROM sync_control.sync_run
                WHERE sync_run_id = %s;
                """,
                (FAILED_RUN_ID,),
            )

            assert cursor.fetchone() == (
                "failed",
                LOCK_ERROR_MESSAGE,
            )

        test_connection.rollback()

        with psycopg.connect(
            TEST_DATABASE_DSN,
            autocommit=True,
            connect_timeout=5,
        ) as verification_connection:
            with verification_connection.cursor() as cursor:
                cursor.execute(
                    """
                    SELECT
                        (
                            SELECT COUNT(*)
                            FROM central_repository
                                .appointment_type_reference
                            WHERE appointment_type_code = %s
                        ),
                        (
                            SELECT COUNT(*)
                            FROM facility_cache
                                .appointment_type_reference
                            WHERE appointment_type_code = %s
                        ),
                        (
                            SELECT COUNT(*)
                            FROM sync_control.sync_run
                            WHERE sync_run_id IN (%s, %s)
                        );
                    """,
                    (
                        RETRY_CODE,
                        RETRY_CODE,
                        FAILED_RUN_ID,
                        RETRY_RUN_ID,
                    ),
                )

                assert cursor.fetchone() == (0, 0, 0)

                cursor.execute(
                    """
                    SELECT
                        last_source_updated_at,
                        last_source_key,
                        last_successful_sync_run_id
                    FROM sync_control.sync_checkpoint
                    WHERE reference_domain = 'appointment_type';
                    """
                )

                assert cursor.fetchone() == (
                    BASELINE_UPDATED_AT,
                    BASELINE_CODE,
                    BASELINE_RUN_ID,
                )

    finally:
        if test_connection is not None:
            test_connection.rollback()
            test_connection.close()

        if lock_connection is not None:
            lock_connection.rollback()
            lock_connection.close()

        if database_created:
            drop_temp_database()
