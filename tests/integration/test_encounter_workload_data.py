"""Integration tests for deterministic encounter workload data."""

from collections.abc import Iterator

import psycopg
import pytest

from scripts.encounter_workload_data import (
    EncounterWorkloadDataset,
    build_workload_dataset,
    get_database_url,
    prepare_workload_dataset,
    remove_workload_dataset,
    verify_workload_dataset,
)


TEST_STARTING_ENCOUNTER_ID = -910_000
TEST_RECORD_COUNT = 4


def postgres_is_available() -> tuple[bool, str]:
    """Return whether the configured PostgreSQL database is reachable."""

    try:
        with psycopg.connect(
            get_database_url(),
            application_name="encounter-workload-data-test-readiness",
            connect_timeout=3,
        ):
            return True, "PostgreSQL is available"
    except psycopg.Error as error:
        return False, str(error)


@pytest.fixture
def workload_dataset() -> Iterator[EncounterWorkloadDataset]:
    """Provide an isolated dataset and guarantee final cleanup."""

    available, details = postgres_is_available()

    if not available:
        pytest.skip(
            "PostgreSQL is unavailable for encounter workload "
            f"integration testing: {details}"
        )

    dataset = build_workload_dataset(
        TEST_RECORD_COUNT,
        starting_encounter_id=TEST_STARTING_ENCOUNTER_ID,
        encounter_type="encounter_workload_data_test",
    )

    remove_workload_dataset(dataset)

    try:
        yield dataset
    finally:
        remove_workload_dataset(dataset)


@pytest.mark.integration
def test_prepare_workload_dataset_creates_clean_scheduled_state(
    workload_dataset: EncounterWorkloadDataset,
) -> None:
    """Verify preparation creates the exact clean scheduled dataset."""

    result = prepare_workload_dataset(workload_dataset)

    assert result["dataset"] == {
        "record_count": TEST_RECORD_COUNT,
        "encounter_ids": list(workload_dataset.encounter_ids),
        "encounter_date": workload_dataset.encounter_date.isoformat(),
        "encounter_type": workload_dataset.encounter_type,
    }

    assert result["insertion"] == {
        "encounters_inserted": TEST_RECORD_COUNT,
        "setup_audit_rows_deleted": TEST_RECORD_COUNT,
    }

    assert result["verification"] == {
        "record_count": TEST_RECORD_COUNT,
        "scheduled_count": TEST_RECORD_COUNT,
        "audit_row_count": 0,
        "first_encounter_id": workload_dataset.encounter_ids[0],
        "last_encounter_id": workload_dataset.encounter_ids[-1],
        "valid": True,
    }


@pytest.mark.integration
def test_remove_workload_dataset_removes_encounters_and_cleanup_audits(
    workload_dataset: EncounterWorkloadDataset,
) -> None:
    """Verify cleanup leaves no encounters or generated audit records."""

    prepare_workload_dataset(workload_dataset)

    cleanup = remove_workload_dataset(workload_dataset)

    assert cleanup == {
        "encounters_deleted": TEST_RECORD_COUNT,
        "audit_rows_deleted": TEST_RECORD_COUNT,
    }

    with pytest.raises(
        RuntimeError,
        match="Prepared encounter identifiers do not match",
    ):
        verify_workload_dataset(workload_dataset)

    second_cleanup = remove_workload_dataset(workload_dataset)

    assert second_cleanup == {
        "encounters_deleted": 0,
        "audit_rows_deleted": 0,
    }