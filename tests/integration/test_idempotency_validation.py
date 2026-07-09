import os
import subprocess
import uuid

import pytest
import requests


API_BASE_URL = os.getenv("SDET_API_BASE_URL", "http://localhost:8000")


def api_is_available() -> bool:
    """
    Return True when the local API is reachable.

    This allows the integration test to skip cleanly when Docker Compose
    services are not running, such as in lightweight local or CI runs.
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=3)
        return response.status_code == 200
    except requests.RequestException:
        return False


def delete_idempotency_key(idempotency_key: str) -> None:
    """
    Best-effort cleanup for the synthetic idempotency key created by this test.

    The test uses a unique key, so cleanup is not required for correctness,
    but cleanup keeps the local development table from growing unnecessarily.
    """
    subprocess.run(
        [
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
            "-c",
            (
                "DELETE FROM idempotency_keys "
                f"WHERE idempotency_key = '{idempotency_key}';"
            ),
        ],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


@pytest.mark.integration
def test_idempotency_endpoint_creates_replays_and_rejects_conflict():
    """
    Validate retry-safe API behavior for idempotent write-style requests.

    Expected behavior:
    - First request with a new Idempotency-Key stores the original response.
    - Retry with the same key and same body returns the original response.
    - Retry with the same key but different body returns HTTP 409 Conflict.
    """

    if not api_is_available():
        pytest.skip(
            "Local API is not available. Start Docker Compose services before "
            "running idempotency integration validation."
        )

    idempotency_key = f"idempotency-test-{uuid.uuid4()}"
    headers = {"Idempotency-Key": idempotency_key}

    original_payload = {
        "patient_id": 1001,
        "encounter_type": "primary_care",
    }

    conflicting_payload = {
        "patient_id": 2002,
        "encounter_type": "urgent_care",
    }

    try:
        first_response = requests.post(
            f"{API_BASE_URL}/qa/idempotency-validation",
            headers=headers,
            json=original_payload,
            timeout=5,
        )

        if first_response.status_code == 404:
            pytest.skip(
                "Idempotency QA endpoint is disabled or unavailable. "
                "Set ENABLE_QA_ENDPOINTS=true when running this integration test."
            )

        assert first_response.status_code == 200, first_response.text

        first_body = first_response.json()

        assert first_body["validation"] == "idempotency_created"
        assert first_body["idempotency_key"] == idempotency_key
        assert first_body["response_status"] == 201
        assert first_body["replayed"] is False
        assert first_body["replayed_count"] == 0
        assert first_body["response_body"]["status"] == "created"
        assert (
            first_body["response_body"]["synthetic_operation"]
            == "create_encounter"
        )

        first_result_id = first_body["response_body"]["synthetic_result_id"]
        first_request_hash = first_body["request_hash"]

        replay_response = requests.post(
            f"{API_BASE_URL}/qa/idempotency-validation",
            headers=headers,
            json=original_payload,
            timeout=5,
        )

        assert replay_response.status_code == 200

        replay_body = replay_response.json()

        assert replay_body["validation"] == "idempotency_replayed"
        assert replay_body["idempotency_key"] == idempotency_key
        assert replay_body["response_status"] == 201
        assert replay_body["replayed"] is True
        assert replay_body["replayed_count"] == 1
        assert replay_body["request_hash"] == first_request_hash
        assert (
            replay_body["response_body"]["synthetic_result_id"]
            == first_result_id
        )

        conflict_response = requests.post(
            f"{API_BASE_URL}/qa/idempotency-validation",
            headers=headers,
            json=conflicting_payload,
            timeout=5,
        )

        assert conflict_response.status_code == 409

        conflict_body = conflict_response.json()

        assert conflict_body["detail"]["validation"] == "idempotency_conflict"
        assert conflict_body["detail"]["idempotency_key"] == idempotency_key
        assert (
            conflict_body["detail"]["stored_request_hash"]
            == first_request_hash
        )
        assert (
            conflict_body["detail"]["incoming_request_hash"]
            != first_request_hash
        )

    finally:
        delete_idempotency_key(idempotency_key)