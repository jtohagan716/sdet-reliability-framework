from __future__ import annotations

import time
from typing import Any

from api_service.database import get_connection
from api_service.database_timings import DatabasePhaseTimings
from api_service.observability.audit_context import (
    get_current_trace_ids,
    set_postgres_audit_values,
)


MAX_BATCH_SIZE = 100

BACKGROUND_REQUEST_METHOD = "BACKGROUND"
BACKGROUND_REQUEST_PATH = "/background/encounter-batches"
BACKGROUND_SERVICE_NAME = "sdet-reliability-background-worker"
BACKGROUND_CHANGE_SOURCE = "background_workload"


class EncounterBatchProcessingError(RuntimeError):
    """Raised when an encounter batch cannot be completed atomically."""


def process_scheduled_encounter_batch(
    *,
    batch_size: int,
    worker_id: str,
    batch_id: str,
    timings: DatabasePhaseTimings | None = None,
    inject_failure_after_update: bool = False,
) -> dict[str, Any]:
    """
    Atomically process one deterministic batch of scheduled encounters.

    Eligible encounters are selected in encounter_id order and locked with
    FOR UPDATE SKIP LOCKED so concurrent workers cannot process the same row.

    The encounter audit trigger records each scheduled-to-completed transition.
    Any failure before the connection context exits rolls back the full batch.
    """

    if batch_size < 1 or batch_size > MAX_BATCH_SIZE:
        raise ValueError(
            f"batch_size must be between 1 and {MAX_BATCH_SIZE}"
        )

    resolved_worker_id = worker_id.strip()
    resolved_batch_id = batch_id.strip()

    if not resolved_worker_id:
        raise ValueError("worker_id must not be empty")

    if not resolved_batch_id:
        raise ValueError("batch_id must not be empty")

    resolved_timings = timings or DatabasePhaseTimings()

    query_ms = 0.0
    fetch_ms = 0.0

    selected_encounter_ids: list[int] = []
    updated_encounter_ids: list[int] = []
    audit_rows: list[dict[str, Any]] = []

    trace_id, span_id = get_current_trace_ids()

    with get_connection(timings=resolved_timings) as connection:
        try:
            query_started = time.perf_counter()

            set_postgres_audit_values(
                connection,
                trace_id=trace_id,
                span_id=span_id,
                request_id=resolved_batch_id,
                request_method=BACKGROUND_REQUEST_METHOD,
                request_path=BACKGROUND_REQUEST_PATH,
                service_name=BACKGROUND_SERVICE_NAME,
                changed_by=resolved_worker_id,
                change_source=BACKGROUND_CHANGE_SOURCE,
            )

            query_ms += (
                time.perf_counter() - query_started
            ) * 1000

            with connection.cursor() as cursor:
                query_started = time.perf_counter()

                cursor.execute(
                    """
                    SELECT encounter_id
                    FROM encounters
                    WHERE status = 'scheduled'
                    ORDER BY encounter_id
                    FOR UPDATE SKIP LOCKED
                    LIMIT %s
                    """,
                    (batch_size,),
                )

                query_ms += (
                    time.perf_counter() - query_started
                ) * 1000

                fetch_started = time.perf_counter()
                selected_rows = cursor.fetchall()

                fetch_ms += (
                    time.perf_counter() - fetch_started
                ) * 1000

                selected_encounter_ids = [
                    row["encounter_id"]
                    for row in selected_rows
                ]

                if selected_encounter_ids:
                    query_started = time.perf_counter()

                    cursor.execute(
                        """
                        UPDATE encounters
                        SET status = 'completed'
                        WHERE encounter_id = ANY(%s::int[])
                          AND status = 'scheduled'
                        RETURNING encounter_id
                        """,
                        (selected_encounter_ids,),
                    )

                    query_ms += (
                        time.perf_counter() - query_started
                    ) * 1000

                    fetch_started = time.perf_counter()
                    updated_rows = cursor.fetchall()

                    fetch_ms += (
                        time.perf_counter() - fetch_started
                    ) * 1000

                    updated_encounter_ids = sorted(
                        row["encounter_id"]
                        for row in updated_rows
                    )

                    if (
                        updated_encounter_ids
                        != selected_encounter_ids
                    ):
                        raise EncounterBatchProcessingError(
                            "Selected and updated encounter IDs "
                            "did not match"
                        )

                    if inject_failure_after_update:
                        raise EncounterBatchProcessingError(
                            "Injected failure after encounter update"
                        )

                    query_started = time.perf_counter()

                    cursor.execute(
                        """
                        SELECT
                            audit_id,
                            encounter_id,
                            operation_type,
                            old_status,
                            new_status,
                            changed_by,
                            change_source,
                            trace_id,
                            span_id,
                            request_id,
                            request_method,
                            request_path,
                            service_name,
                            changed_at
                        FROM encounter_audit
                        WHERE encounter_id = ANY(%s::int[])
                          AND operation_type = 'UPDATE'
                          AND request_id = %s
                        ORDER BY encounter_id, audit_id
                        """,
                        (
                            updated_encounter_ids,
                            resolved_batch_id,
                        ),
                    )

                    query_ms += (
                        time.perf_counter() - query_started
                    ) * 1000

                    fetch_started = time.perf_counter()
                    audit_rows = list(cursor.fetchall())

                    fetch_ms += (
                        time.perf_counter() - fetch_started
                    ) * 1000

                    if len(audit_rows) != len(
                        updated_encounter_ids
                    ):
                        raise EncounterBatchProcessingError(
                            "Audit row count did not match "
                            "updated encounter count"
                        )

                    for audit_row in audit_rows:
                        if (
                            audit_row["old_status"] != "scheduled"
                            or audit_row["new_status"]
                            != "completed"
                            or audit_row["changed_by"]
                            != resolved_worker_id
                            or audit_row["change_source"]
                            != BACKGROUND_CHANGE_SOURCE
                            or audit_row["request_id"]
                            != resolved_batch_id
                        ):
                            raise EncounterBatchProcessingError(
                                "Encounter audit metadata "
                                "validation failed"
                            )
        finally:
            resolved_timings.query_ms = query_ms
            resolved_timings.fetch_ms = fetch_ms

    return {
        "batch_id": resolved_batch_id,
        "worker_id": resolved_worker_id,
        "requested_batch_size": batch_size,
        "selected_count": len(selected_encounter_ids),
        "updated_count": len(updated_encounter_ids),
        "audit_count": len(audit_rows),
        "encounter_ids": updated_encounter_ids,
        "status_transition": {
            "from": "scheduled",
            "to": "completed",
        },
        "trace_id": trace_id,
        "span_id": span_id,
        "database_timings": resolved_timings.as_dict(),
        "audit_rows": audit_rows,
    }