import requests


BASE_URL = "http://127.0.0.1:8000"


def test_echo_service_normal_mode():
    response = requests.get(
        f"{BASE_URL}/echo?mode=normal",
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "echo"
    assert data["mode"] == "normal"
    assert 100 <= data["simulated_latency_ms"] <= 500


def test_echo_service_slow_mode():
    response = requests.get(
        f"{BASE_URL}/echo?mode=slow",
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "echo"
    assert data["mode"] == "slow"
    assert 1000 <= data["simulated_latency_ms"] <= 2000


def test_echo_service_degraded_mode():
    response = requests.get(
        f"{BASE_URL}/echo?mode=degraded",
        timeout=6,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "echo"
    assert data["mode"] == "degraded"
    assert 2500 <= data["simulated_latency_ms"] <= 4000


def test_echo_service_fail_mode():
    response = requests.get(
        f"{BASE_URL}/echo?mode=fail",
        timeout=5,
    )

    assert response.status_code == 200

    data = response.json()

    assert data["message"] == "service_failure"
    assert data["status"] == "ERROR"