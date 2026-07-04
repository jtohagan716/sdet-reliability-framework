from datetime import date, datetime

from fastapi.testclient import TestClient

from api_service.app import app


client = TestClient(app)


EXPECTED_PATIENT_FIELDS = {
    "patient_id",
    "name",
    "status",
    "last_visit",
}

ALLOWED_PATIENT_STATUSES = {
    "active",
    "inactive",
}


def assert_iso_date(value: str) -> None:
    """Confirm that a value is a valid ISO date string in YYYY-MM-DD format."""
    assert isinstance(value, str)
    parsed = date.fromisoformat(value)
    assert parsed.isoformat() == value


def assert_iso_datetime(value: str) -> None:
    """Confirm that a value is a valid ISO datetime string."""
    assert isinstance(value, str)
    datetime.fromisoformat(value.replace("Z", "+00:00"))


def assert_patient_contract(payload: dict, expected_patient_id: int) -> None:
    """Validate the stable response contract for a synthetic patient lookup."""
    assert isinstance(payload, dict)

    assert set(payload.keys()) == EXPECTED_PATIENT_FIELDS

    assert type(payload["patient_id"]) is int
    assert payload["patient_id"] == expected_patient_id

    assert isinstance(payload["name"], str)
    assert payload["name"].strip() != ""

    assert isinstance(payload["status"], str)
    assert payload["status"] in ALLOWED_PATIENT_STATUSES

    assert_iso_date(payload["last_visit"])


def test_health_response_contract():
    response = client.get("/health")

    assert response.status_code == 200

    payload = response.json()

    assert isinstance(payload, dict)
    assert set(payload.keys()) == {"status", "timestamp_utc"}

    assert payload["status"] == "UP"
    assert_iso_datetime(payload["timestamp_utc"])


def test_patient_1001_response_contract():
    response = client.get("/patients/1001")

    assert response.status_code == 200

    payload = response.json()

    assert_patient_contract(payload, expected_patient_id=1001)


def test_patient_1002_response_contract():
    response = client.get("/patients/1002")

    assert response.status_code == 200

    payload = response.json()

    assert_patient_contract(payload, expected_patient_id=1002)


def test_missing_patient_error_contract():
    response = client.get("/patients/9999")

    assert response.status_code == 404

    payload = response.json()

    assert isinstance(payload, dict)
    assert set(payload.keys()) == {"detail"}
    assert isinstance(payload["detail"], str)
    assert payload["detail"].strip() != ""


def test_invalid_patient_id_error_contract():
    response = client.get("/patients/abc")

    assert response.status_code == 422

    payload = response.json()

    assert isinstance(payload, dict)
    assert set(payload.keys()) == {"detail"}
    assert isinstance(payload["detail"], list)
    assert len(payload["detail"]) >= 1

    first_error = payload["detail"][0]

    assert isinstance(first_error, dict)
    assert "loc" in first_error
    assert "msg" in first_error
    assert "type" in first_error

    assert "patient_id" in [str(location_part) for location_part in first_error["loc"]]
    assert isinstance(first_error["msg"], str)
    assert isinstance(first_error["type"], str)
