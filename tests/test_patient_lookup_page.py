from fastapi.testclient import TestClient

from api_service.app import app


client = TestClient(app)


def test_patient_lookup_page_returns_accessible_html():
    response = client.get("/patient-lookup")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]

    body = response.text

    assert "<title>Patient Lookup</title>" in body
    assert '<html lang="en">' in body
    assert "<h1>Patient Lookup</h1>" in body
    assert '<label for="patient-id">Patient ID</label>' in body
    assert 'id="patient-id"' in body
    assert "Lookup Patient" in body
    assert 'aria-live="polite"' in body
    assert 'aria-label="Lookup result"' in body