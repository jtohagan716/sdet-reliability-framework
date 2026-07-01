from fastapi.testclient import TestClient

from api_service.app import app


client = TestClient(app)


SENSITIVE_FIELDS = {
    "ssn",
    "social_security_number",
    "password",
    "token",
    "api_key",
    "secret",
    "diagnosis",
    "real_address",
    "production_system_id",
    "medical_record_number",
}


def test_get_patient_summary_valid_patient_1001_returns_expected_response():
    response = client.get("/patients/1001")

    assert response.status_code == 200

    data = response.json()

    assert data["patient_id"] == 1001
    assert data["name"] == "Alex Morgan"
    assert data["status"] == "active"
    assert data["last_visit"] == "2026-06-15"

    assert SENSITIVE_FIELDS.isdisjoint(data.keys())


def test_get_patient_summary_valid_patient_1002_returns_distinct_response():
    response = client.get("/patients/1002")

    assert response.status_code == 200

    data = response.json()

    assert data["patient_id"] == 1002
    assert data["name"] == "Jordan Lee"
    assert data["status"] == "inactive"
    assert data["last_visit"] == "2026-05-20"

    assert SENSITIVE_FIELDS.isdisjoint(data.keys())


def test_get_patient_summary_unknown_patient_returns_404():
    response = client.get("/patients/9999")

    assert response.status_code == 404

    data = response.json()

    assert "detail" in data
    assert data["detail"] == "Synthetic patient 9999 not found"


def test_get_patient_summary_invalid_patient_id_type_returns_422():
    response = client.get("/patients/abc")

    assert response.status_code == 422

    data = response.json()

    assert "detail" in data
    assert isinstance(data["detail"], list)


def test_patient_summary_rejects_unsupported_post_method():
    response = client.post("/patients/1001")

    assert response.status_code == 405

    data = response.json()

    assert "detail" in data


def test_openapi_contract_documents_patient_endpoint():
    response = client.get("/openapi.json")

    assert response.status_code == 200

    openapi = response.json()

    assert "paths" in openapi
    assert "/patients/{patient_id}" in openapi["paths"]
    assert "get" in openapi["paths"]["/patients/{patient_id}"]


def test_patient_summary_response_model_excludes_sensitive_fields():
    response = client.get("/patients/1001")

    assert response.status_code == 200

    data = response.json()

    for sensitive_field in SENSITIVE_FIELDS:
        assert sensitive_field not in data