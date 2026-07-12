from __future__ import annotations

import time
from typing import Any

from api_service.database import get_connection
from api_service.database_timings import DatabasePhaseTimings


def get_patient_summary_from_postgres(
    patient_id: int,
    defect_mode: str = "none",
    timings: DatabasePhaseTimings | None = None,
) -> dict[str, Any] | None:
    if defect_mode == "include_scheduled_last_visit":
        encounter_status_filter = ""
    else:
        encounter_status_filter = "AND e.status = 'completed'"

    query = f"""
        SELECT
            p.patient_id,
            p.first_name || ' ' || p.last_name AS name,
            p.status,
            COALESCE(
                TO_CHAR(MAX(e.encounter_date), 'YYYY-MM-DD'),
                ''
            ) AS last_visit
        FROM patients p
        LEFT JOIN encounters e
            ON p.patient_id = e.patient_id
           {encounter_status_filter}
        WHERE p.patient_id = %s
        GROUP BY
            p.patient_id,
            p.first_name,
            p.last_name,
            p.status
    """

    with get_connection(timings=timings) as connection:
        with connection.cursor() as cursor:
            query_started = time.perf_counter()
            cursor.execute(query, (patient_id,))

            if timings is not None:
                timings.query_ms = (
                    time.perf_counter() - query_started
                ) * 1000

            fetch_started = time.perf_counter()
            row = cursor.fetchone()

            if timings is not None:
                timings.fetch_ms = (
                    time.perf_counter() - fetch_started
                ) * 1000

    if row is None:
        return None

    return dict(row)
