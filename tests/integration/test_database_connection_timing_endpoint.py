import os

import pytest
import requests


API_BASE_URL = os.getenv(
    "SDET_API_BASE_URL",
    "http://localhost:8000",
)


def test_database_connection_timing_endpoint_reports_valid_phases():
    endpoint = (
        f"{API_BASE_URL}/qa/database-connection-timing"
        "?patient_id=1001"
    )

    try:
        response = requests.get(endpoint, timeout=10)
    except requests.RequestException as exc:
        pytest.skip(
            f"API stack is unavailable for database timing validation: {exc}"
        )

    if response.status_code == 404:
        pytest.skip(
            "Database timing QA endpoint is unavailable or disabled"
        )

    assert response.status_code == 200, response.text

    payload = response.json()

    assert payload["patient_id"] == 1001
    assert (
        payload["connection_strategy"]
        == "connection_per_operation"
    )

    phases = payload["database_phases"]

    expected_phase_names = {
        "connect_ms",
        "query_ms",
        "fetch_ms",
        "close_ms",
        "total_ms",
    }

    assert set(phases) == expected_phase_names

    for phase_name in expected_phase_names:
        assert isinstance(phases[phase_name], (int, float))
        assert phases[phase_name] >= 0

    measured_phase_total = (
        phases["connect_ms"]
        + phases["query_ms"]
        + phases["fetch_ms"]
        + phases["close_ms"]
    )

    # Allow a small rounding margin because values are rounded
    # independently before being returned by the endpoint.
    assert phases["total_ms"] + 0.5 >= measured_phase_total
