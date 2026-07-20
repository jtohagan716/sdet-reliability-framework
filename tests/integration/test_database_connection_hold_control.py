import os

import pytest
import requests


API_BASE_URL = os.getenv(
    "SDET_API_BASE_URL",
    "http://localhost:8000",
)

TIMING_ENDPOINT = (
    f"{API_BASE_URL}/qa/database-connection-timing"
)


def _request_timing(
    *,
    connection_hold_ms: int | None = None,
) -> requests.Response:
    params = {"patient_id": 1001}

    if connection_hold_ms is not None:
        params["connection_hold_ms"] = connection_hold_ms

    try:
        response = requests.get(
            TIMING_ENDPOINT,
            params=params,
            timeout=10,
        )
    except requests.RequestException as exc:
        pytest.skip(
            "API stack is unavailable for controlled "
            f"connection-hold validation: {exc}"
        )

    if response.status_code == 404:
        pytest.skip(
            "Database timing QA endpoint is unavailable or disabled"
        )

    return response


def test_database_connection_timing_defaults_to_zero_hold():
    response = _request_timing()

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["patient_id"] == 1001
    assert payload["connection_hold_ms"] == 0


def test_database_connection_timing_applies_controlled_hold():
    requested_hold_ms = 100

    response = _request_timing(
        connection_hold_ms=requested_hold_ms,
    )

    assert response.status_code == 200, response.text

    payload = response.json()
    phases = payload["database_phases"]

    assert payload["patient_id"] == 1001
    assert payload["connection_hold_ms"] == requested_hold_ms

    measured_phase_total = (
        phases["acquire_ms"]
        + phases["query_ms"]
        + phases["fetch_ms"]
        + phases["release_ms"]
    )

    unassigned_elapsed_ms = (
        phases["total_ms"]
        - measured_phase_total
    )

    # The controlled hold occurs after acquisition and before query
    # execution. It therefore appears in total_ms without inflating
    # acquire_ms or query_ms.
    assert phases["total_ms"] >= requested_hold_ms
    assert unassigned_elapsed_ms >= requested_hold_ms - 10


def test_database_connection_timing_rejects_excessive_hold():
    response = _request_timing(
        connection_hold_ms=1001,
    )

    assert response.status_code == 422

    assert response.json() == {
        "detail": (
            "connection_hold_ms must be between "
            "0 and 1000 milliseconds"
        )
    }
