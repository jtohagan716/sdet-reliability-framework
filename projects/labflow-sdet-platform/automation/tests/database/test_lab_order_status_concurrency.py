import queue
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

import psycopg
import pytest
from psycopg.conninfo import make_conninfo


LOCK_WAIT_TIMEOUT_SECONDS = 5.0
LOCK_POLL_INTERVAL_SECONDS = 0.05


def _connection_info(
    database_url: str,
    application_name: str,
) -> str:
    return make_conninfo(
        database_url,
        application_name=application_name,
    )


def _insert_committed_lab_order(
    database_url: str,
    clinical_context: dict[str, object],
) -> uuid.UUID:
    lab_order_id = uuid.uuid4()
    unique_suffix = lab_order_id.hex[:12].upper()

    connection_info = _connection_info(
        database_url,
        "labflow-concurrency-setup",
    )

    with psycopg.connect(
        connection_info,
        autocommit=True,
    ) as connection:
        connection.execute(
            """
            INSERT INTO public.lab_orders (
                id,
                placer_order_number,
                synthetic_patient_id,
                patient_id,
                encounter_id,
                test_code,
                priority,
                status,
                ordered_at,
                created_at
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                %s,
                NOW(),
                NOW()
            )
            """,
            (
                lab_order_id,
                f"DB-CONCURRENCY-{unique_suffix}",
                clinical_context["synthetic_patient_id"],
                clinical_context["patient_id"],
                clinical_context["encounter_id"],
                "CBC",
                "ROUTINE",
                "PLACED",
            ),
        )

    return lab_order_id


def _transition_lab_order_status(
    connection: psycopg.Connection,
    lab_order_id: uuid.UUID,
    requested_status: str,
) -> str:
    row = connection.execute(
        """
        SELECT public.transition_lab_order_status(
            %s,
            %s::public.lab_order_status
        )
        """,
        (
            lab_order_id,
            requested_status,
        ),
    ).fetchone()

    assert row is not None

    return str(row[0])


def _transition_and_commit(
    database_url: str,
    lab_order_id: uuid.UUID,
    requested_status: str,
    backend_pid_queue: queue.Queue[int],
) -> str:
    connection_info = _connection_info(
        database_url,
        "labflow-concurrency-transaction-b",
    )

    with psycopg.connect(connection_info) as connection:
        connection.execute(
            "SET LOCAL lock_timeout = '5s'"
        )
        connection.execute(
            "SET LOCAL statement_timeout = '10s'"
        )

        backend_pid_queue.put(
            connection.info.backend_pid
        )

        resulting_status = _transition_lab_order_status(
            connection,
            lab_order_id,
            requested_status,
        )

        connection.commit()

        return resulting_status


def _wait_until_blocked_by(
    observer_connection: psycopg.Connection,
    waiting_backend_pid: int,
    expected_blocker_backend_pid: int,
) -> None:
    deadline = time.monotonic() + LOCK_WAIT_TIMEOUT_SECONDS
    latest_observation: tuple[object, ...] | None = None

    while time.monotonic() < deadline:
        row = observer_connection.execute(
            """
            SELECT
                state,
                wait_event_type,
                pg_blocking_pids(%s)
            FROM pg_stat_activity
            WHERE pid = %s
            """,
            (
                waiting_backend_pid,
                waiting_backend_pid,
            ),
        ).fetchone()

        latest_observation = row

        if row is not None:
            state = row[0]
            wait_event_type = row[1]
            blocking_backend_pids = row[2]

            if (
                state == "active"
                and wait_event_type == "Lock"
                and expected_blocker_backend_pid
                in blocking_backend_pids
            ):
                return

        time.sleep(LOCK_POLL_INTERVAL_SECONDS)

    pytest.fail(
        "Transaction B did not enter the expected lock wait. "
        f"Waiting PID: {waiting_backend_pid}; "
        f"expected blocker PID: {expected_blocker_backend_pid}; "
        f"latest observation: {latest_observation}"
    )
def _read_final_status(
    connection: psycopg.Connection,
    lab_order_id: uuid.UUID,
) -> str:
    row = connection.execute(
        """
        SELECT status::text
        FROM public.lab_orders
        WHERE id = %s
        """,
        (lab_order_id,),
    ).fetchone()

    assert row is not None

    return str(row[0])


def _read_status_history(
    connection: psycopg.Connection,
    lab_order_id: uuid.UUID,
) -> list[tuple[str, str]]:
    rows = connection.execute(
        """
        SELECT
            previous_status::text,
            new_status::text
        FROM public.lab_order_status_audit
        WHERE lab_order_id = %s
        ORDER BY id
        """,
        (lab_order_id,),
    ).fetchall()

    return [
        (
            str(previous_status),
            str(new_status),
        )
        for previous_status, new_status in rows
    ]
def test_competing_status_transitions_are_serialized(
    database_url: str,
    clinical_context: dict[str, object],
) -> None:
    lab_order_id = _insert_committed_lab_order(
        database_url,
        clinical_context,
    )

    transaction_a_connection_info = _connection_info(
        database_url,
        "labflow-concurrency-transaction-a",
    )
    observer_connection_info = _connection_info(
        database_url,
        "labflow-concurrency-observer",
    )

    transaction_b_pid_queue: queue.Queue[int] = queue.Queue(
        maxsize=1
    )

    transaction_a_connection = psycopg.connect(
        transaction_a_connection_info
    )
    observer_connection = psycopg.connect(
        observer_connection_info,
        autocommit=True,
    )
    executor = ThreadPoolExecutor(max_workers=1)

    try:
        transaction_a_connection.execute(
            "SET LOCAL lock_timeout = '5s'"
        )
        transaction_a_connection.execute(
            "SET LOCAL statement_timeout = '10s'"
        )

        transaction_a_backend_pid = (
            transaction_a_connection.info.backend_pid
        )

        transaction_a_status = _transition_lab_order_status(
            transaction_a_connection,
            lab_order_id,
            "IN_PROGRESS",
        )

        assert transaction_a_status == "IN_PROGRESS"

        transaction_b_future = executor.submit(
            _transition_and_commit,
            database_url,
            lab_order_id,
            "COMPLETED",
            transaction_b_pid_queue,
        )

        try:
            transaction_b_backend_pid = (
                transaction_b_pid_queue.get(
                    timeout=LOCK_WAIT_TIMEOUT_SECONDS
                )
            )
        except queue.Empty:
            pytest.fail(
                "Transaction B did not report its PostgreSQL "
                "backend PID."
            )

        _wait_until_blocked_by(
            observer_connection,
            waiting_backend_pid=transaction_b_backend_pid,
            expected_blocker_backend_pid=(
                transaction_a_backend_pid
            ),
        )

        assert not transaction_b_future.done()

        transaction_a_connection.commit()

        transaction_b_status = transaction_b_future.result(
            timeout=LOCK_WAIT_TIMEOUT_SECONDS
        )

        assert transaction_b_status == "COMPLETED"

        final_status = _read_final_status(
            observer_connection,
            lab_order_id,
        )
        status_history = _read_status_history(
            observer_connection,
            lab_order_id,
        )

        assert final_status == "COMPLETED"
        assert status_history == [
            ("PLACED", "IN_PROGRESS"),
            ("IN_PROGRESS", "COMPLETED"),
        ]

    finally:
        transaction_a_connection.rollback()
        transaction_a_connection.close()
        observer_connection.close()

        executor.shutdown(
            wait=True,
            cancel_futures=True,
        )
def test_waiting_transition_is_revalidated_after_blocker_commits(
    database_url: str,
    clinical_context: dict[str, object],
) -> None:
    lab_order_id = _insert_committed_lab_order(
        database_url,
        clinical_context,
    )

    transaction_a_connection_info = _connection_info(
        database_url,
        "labflow-concurrency-invalidating-transaction-a",
    )
    observer_connection_info = _connection_info(
        database_url,
        "labflow-concurrency-invalidating-observer",
    )

    transaction_b_pid_queue: queue.Queue[int] = queue.Queue(
        maxsize=1
    )

    transaction_a_connection = psycopg.connect(
        transaction_a_connection_info
    )
    observer_connection = psycopg.connect(
        observer_connection_info,
        autocommit=True,
    )
    executor = ThreadPoolExecutor(max_workers=1)

    try:
        transaction_a_connection.execute(
            "SET LOCAL lock_timeout = '5s'"
        )
        transaction_a_connection.execute(
            "SET LOCAL statement_timeout = '10s'"
        )

        transaction_a_backend_pid = (
            transaction_a_connection.info.backend_pid
        )

        transaction_a_status = _transition_lab_order_status(
            transaction_a_connection,
            lab_order_id,
            "CANCELLED",
        )

        assert transaction_a_status == "CANCELLED"

        transaction_b_future = executor.submit(
            _transition_and_commit,
            database_url,
            lab_order_id,
            "IN_PROGRESS",
            transaction_b_pid_queue,
        )

        try:
            transaction_b_backend_pid = (
                transaction_b_pid_queue.get(
                    timeout=LOCK_WAIT_TIMEOUT_SECONDS
                )
            )
        except queue.Empty:
            pytest.fail(
                "Transaction B did not report its PostgreSQL "
                "backend PID."
            )

        _wait_until_blocked_by(
            observer_connection,
            waiting_backend_pid=transaction_b_backend_pid,
            expected_blocker_backend_pid=(
                transaction_a_backend_pid
            ),
        )

        assert not transaction_b_future.done()

        transaction_a_connection.commit()

        with pytest.raises(
            psycopg.errors.CheckViolation
        ) as error_info:
            transaction_b_future.result(
                timeout=LOCK_WAIT_TIMEOUT_SECONDS
            )

        assert error_info.value.sqlstate == "23514"

        final_status = _read_final_status(
            observer_connection,
            lab_order_id,
        )
        status_history = _read_status_history(
            observer_connection,
            lab_order_id,
        )

        assert final_status == "CANCELLED"
        assert status_history == [
            ("PLACED", "CANCELLED"),
        ]

    finally:
        transaction_a_connection.rollback()
        transaction_a_connection.close()
        observer_connection.close()

        executor.shutdown(
            wait=True,
            cancel_futures=True,
        )