import pytest


pytestmark = [
    pytest.mark.smoke,
    pytest.mark.regression,
]


def test_liveness_endpoint_returns_alive(
    health_client,
):
    response = health_client.get_liveness()

    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_readiness_endpoint_returns_ready(
    health_client,
):
    response = health_client.get_readiness()

    assert response.status_code == 200
    assert response.json()["status"] == "ready"