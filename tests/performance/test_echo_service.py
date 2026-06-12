import requests


def test_echo_service_latency():

    response = requests.get(
        "http://127.0.0.1:8000/echo",
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "echo"

    assert data["simulated_latency_ms"] >= 100

    assert data["simulated_latency_ms"] <= 1200