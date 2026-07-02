from fastapi.testclient import TestClient

from api_service.app import app


client = TestClient(app)


def test_metrics_expose_http_request_counts_with_route_template():
    response = client.get("/patients/1001")
    assert response.status_code == 200

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    assert "sdet_http_requests_total" in metrics_response.text
    assert 'path="/patients/{patient_id}"' in metrics_response.text
    assert 'path="/patients/1001"' not in metrics_response.text


def test_metrics_expose_patient_lookup_outcomes():
    success_response = client.get("/patients/1001")
    not_found_response = client.get("/patients/9999")

    assert success_response.status_code == 200
    assert not_found_response.status_code == 404

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    assert 'sdet_patient_lookup_total{outcome="success"}' in metrics_response.text
    assert 'sdet_patient_lookup_total{outcome="not_found"}' in metrics_response.text


def test_metrics_expose_request_duration_histogram():
    response = client.get("/health")
    assert response.status_code == 200

    metrics_response = client.get("/metrics")

    assert metrics_response.status_code == 200
    assert "sdet_http_request_duration_seconds" in metrics_response.text
    assert "sdet_http_request_duration_seconds_bucket" in metrics_response.text
    assert "sdet_http_request_duration_seconds_count" in metrics_response.text
    assert "sdet_http_request_duration_seconds_sum" in metrics_response.text