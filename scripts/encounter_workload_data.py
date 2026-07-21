from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import date
from typing import Any

import psycopg


DEFAULT_DATABASE_URL = (
    "postgresql://sdet_user:sdet_password@"
    "localhost:5432/sdet_reliability"
)

DEFAULT_STARTING_ENCOUNTER_ID = -900_000
DEFAULT_ENCOUNTER_DATE = date(2026, 7, 21)

DATA_PREPARATION_APPLICATION_NAME = (
    "foreground-background-study-data-prep"
)


@dataclass(frozen=True)
class EncounterWorkloadDataset:
    """Describe the deterministic encounters reserved for one study run."""

    encounter_ids: tuple[int, ...]
    encounter_date: date
    encounter_type: str

    @property
    def record_count(self) -> int:
        """Return the number of encounters in the dataset."""

        return len(self.encounter_ids)


def get_database_url() -> str:
    """Return the configured PostgreSQL connection URL."""

    return os.getenv(
        "DATABASE_URL",
        DEFAULT_DATABASE_URL,
    )


def build_workload_dataset(
    record_count: int,
    *,
    starting_encounter_id: int = DEFAULT_STARTING_ENCOUNTER_ID,
    encounter_date: date = DEFAULT_ENCOUNTER_DATE,
    encounter_type: str = "foreground_background_study",
) -> EncounterWorkloadDataset:
    """Build a deterministic set of reserved encounter identifiers."""

    if record_count <= 0:
        raise ValueError("record_count must be greater than zero")

    if starting_encounter_id >= 0:
        raise ValueError(
            "starting_encounter_id must be negative"
        )

    normalized_encounter_type = encounter_type.strip()

    if not normalized_encounter_type:
        raise ValueError("encounter_type cannot be empty")

    encounter_ids = tuple(
        starting_encounter_id + offset
        for offset in range(record_count)
    )

    if encounter_ids[-1] >= 0:
        raise ValueError(
            "generated encounter identifiers must remain negative"
        )

    return EncounterWorkloadDataset(
        encounter_ids=encounter_ids,
        encounter_date=encounter_date,
        encounter_type=normalized_encounter_type,
    )


def remove_workload_dataset(
    dataset: EncounterWorkloadDataset,
    *,
    database_url: str | None = None,
) -> dict[str, int]:
    """Remove study encounters and every audit row they generated."""

    connection_url = database_url or get_database_url()
    encounter_ids = list(dataset.encounter_ids)

    with psycopg.connect(
        connection_url,
        application_name=DATA_PREPARATION_APPLICATION_NAME,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                DELETE FROM encounters
                WHERE encounter_id = ANY(%s)
                """,
                (encounter_ids,),
            )
            encounters_deleted = cursor.rowcount

            cursor.execute(
                """
                DELETE FROM encounter_audit
                WHERE encounter_id = ANY(%s)
                """,
                (encounter_ids,),
            )
            audit_rows_deleted = cursor.rowcount

    return {
        "encounters_deleted": encounters_deleted,
        "audit_rows_deleted": audit_rows_deleted,
    }


def insert_workload_dataset(
    dataset: EncounterWorkloadDataset,
    *,
    database_url: str | None = None,
) -> dict[str, int]:
    """Insert scheduled study encounters with a clean audit baseline."""

    connection_url = database_url or get_database_url()

    encounter_rows = [
        (
            encounter_id,
            1001,
            501,
            1,
            dataset.encounter_date,
            dataset.encounter_type,
            "scheduled",
        )
        for encounter_id in dataset.encounter_ids
    ]

    with psycopg.connect(
        connection_url,
        application_name=DATA_PREPARATION_APPLICATION_NAME,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.executemany(
                """
                INSERT INTO encounters (
                    encounter_id,
                    patient_id,
                    provider_id,
                    facility_id,
                    encounter_date,
                    encounter_type,
                    status
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s
                )
                """,
                encounter_rows,
            )

            cursor.execute(
                """
                DELETE FROM encounter_audit
                WHERE encounter_id = ANY(%s)
                """,
                (list(dataset.encounter_ids),),
            )
            setup_audit_rows_deleted = cursor.rowcount

    return {
        "encounters_inserted": dataset.record_count,
        "setup_audit_rows_deleted": setup_audit_rows_deleted,
    }


def verify_workload_dataset(
    dataset: EncounterWorkloadDataset,
    *,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Verify the exact scheduled encounter and audit starting state."""

    connection_url = database_url or get_database_url()

    with psycopg.connect(
        connection_url,
        application_name=DATA_PREPARATION_APPLICATION_NAME,
        autocommit=True,
    ) as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    encounter_id,
                    status
                FROM encounters
                WHERE encounter_id = ANY(%s)
                ORDER BY encounter_id
                """,
                (list(dataset.encounter_ids),),
            )
            encounter_rows = cursor.fetchall()

            cursor.execute(
                """
                SELECT COUNT(*)
                FROM encounter_audit
                WHERE encounter_id = ANY(%s)
                """,
                (list(dataset.encounter_ids),),
            )
            audit_row_count = int(cursor.fetchone()[0])

    actual_ids = tuple(
        int(encounter_id)
        for encounter_id, _status in encounter_rows
    )

    expected_ids = tuple(sorted(dataset.encounter_ids))

    if actual_ids != expected_ids:
        raise RuntimeError(
            "Prepared encounter identifiers do not match the "
            f"expected dataset: expected {expected_ids!r}, "
            f"received {actual_ids!r}"
        )

    invalid_status_rows = [
        {
            "encounter_id": int(encounter_id),
            "status": str(status),
        }
        for encounter_id, status in encounter_rows
        if status != "scheduled"
    ]

    if invalid_status_rows:
        raise RuntimeError(
            "Prepared encounters are not all scheduled: "
            f"{invalid_status_rows!r}"
        )

    if audit_row_count != 0:
        raise RuntimeError(
            "Prepared workload dataset contains unexpected audit "
            f"rows: {audit_row_count}"
        )

    return {
        "record_count": len(encounter_rows),
        "scheduled_count": len(encounter_rows),
        "audit_row_count": audit_row_count,
        "first_encounter_id": actual_ids[0],
        "last_encounter_id": actual_ids[-1],
        "valid": True,
    }


def prepare_workload_dataset(
    dataset: EncounterWorkloadDataset,
    *,
    database_url: str | None = None,
) -> dict[str, Any]:
    """Replace existing study data with a verified clean dataset."""

    cleanup = remove_workload_dataset(
        dataset,
        database_url=database_url,
    )

    insertion = insert_workload_dataset(
        dataset,
        database_url=database_url,
    )

    verification = verify_workload_dataset(
        dataset,
        database_url=database_url,
    )

    return {
        "dataset": {
            "record_count": dataset.record_count,
            "encounter_ids": list(dataset.encounter_ids),
            "encounter_date": dataset.encounter_date.isoformat(),
            "encounter_type": dataset.encounter_type,
        },
        "cleanup": cleanup,
        "insertion": insertion,
        "verification": verification,
    }