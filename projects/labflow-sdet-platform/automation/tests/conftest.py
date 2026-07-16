import os
import uuid

import pytest
import requests

from automation.clients.health_client import HealthClient
from automation.clients.lab_orders_client import LabOrdersClient


@pytest.fixture(scope="session")
def base_url():
    configured_url = os.getenv(
        "LABFLOW_BASE_URL",
        "http://localhost:8000",
    )
    return configured_url.rstrip("/")


@pytest.fixture
def lab_order_payload():
    def build_payload(
        *,
        prefix="AUTO",
        synthetic_patient_id="SYN-PAT-AUTO",
        test_code="CBC",
        priority="ROUTINE",
        ordered_at="2026-07-15T18:00:00Z",
        include_priority=True,
        include_test_code=True,
    ):
        unique_suffix = uuid.uuid4().hex[:8]

        payload = {
            "placer_order_number": f"{prefix}-{unique_suffix}",
            "synthetic_patient_id": synthetic_patient_id,
            "ordered_at": ordered_at,
        }

        if include_test_code:
            payload["test_code"] = test_code

        if include_priority:
            payload["priority"] = priority

        return payload

    return build_payload


@pytest.fixture(scope="session")
def api_session():
    with requests.Session() as session:
        session.headers.update(
            {
                "Accept": "application/json",
            }
        )
        yield session


@pytest.fixture(scope="session")
def health_client(
    api_session,
    base_url,
):
    return HealthClient(
        session=api_session,
        base_url=base_url,
    )


@pytest.fixture(scope="session")
def lab_orders_client(
    api_session,
    base_url,
):
    return LabOrdersClient(
        session=api_session,
        base_url=base_url,
    )