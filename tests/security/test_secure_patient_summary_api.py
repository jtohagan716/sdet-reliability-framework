import base64
import json

import requests


BASE_URL = "http://127.0.0.1:8000"
TRUSTED_ISSUER = "https://company-login.com"


def build_test_jwt(payload: dict) -> str:
    header = {
        "alg": "HS256",
        "typ": "JWT",
    }

    def encode(section: dict) -> str:
        raw = json.dumps(section, separators=(",", ":")).encode("utf-8")
        encoded = base64.urlsafe_b64encode(raw).decode("utf-8")
        return encoded.rstrip("=")

    return f"{encode(header)}.{encode(payload)}.fake_signature"


def test_secure_patient_summary_requires_authorization_header():
    response = requests.get(
        f"{BASE_URL}/secure/patient-summary",
        timeout=5,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "MISSING_AUTHORIZATION_HEADER"


def test_secure_patient_summary_rejects_invalid_token():
    response = requests.get(
        f"{BASE_URL}/secure/patient-summary",
        headers={
            "Authorization": "Bearer garbage",
        },
        timeout=5,
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "INVALID_TOKEN"


def test_secure_patient_summary_rejects_wrong_role():
    token = build_test_jwt({
        "sub": "james",
        "role": "admin",
        "iss": TRUSTED_ISSUER,
        "exp": 1890000000,
    })

    response = requests.get(
        f"{BASE_URL}/secure/patient-summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=5,
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "ROLE_NOT_AUTHORIZED"


def test_secure_patient_summary_allows_valid_provider_token():
    token = build_test_jwt({
        "sub": "james",
        "role": "provider",
        "iss": TRUSTED_ISSUER,
        "exp": 1890000000,
    })

    response = requests.get(
        f"{BASE_URL}/secure/patient-summary",
        headers={
            "Authorization": f"Bearer {token}",
        },
        timeout=5,
    )

    assert response.status_code == 200
    assert response.json()["status"] == "ACCESS_GRANTED"
    assert response.json()["subject"] == "james"
    assert response.json()["role"] == "provider"
