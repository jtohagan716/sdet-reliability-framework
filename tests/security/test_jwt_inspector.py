from framework.security.jwt_decoder import decode_jwt
from framework.security.jwt_inspector import (
    inspect_jwt,
    print_jwt_security_report,
)


def test_jwt_inspector_trusts_valid_provider_token():

    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJqYW1lcyIsInJvbGUiOiJwcm92aWRlciIsImV4cCI6MTg5MDAwMDAwMH0."
        "fake_signature"
    )

    decoded = decode_jwt(token)
    result = inspect_jwt(decoded, required_role="provider")

    print_jwt_security_report(result)

    assert result["status"] == "TRUSTED"
    assert result["reason"] == "ACCESS_GRANTED"


def test_jwt_inspector_forbids_wrong_role():

    decoded = {
        "payload": {
            "sub": "james",
            "role": "provider",
            "exp": 1890000000,
        }
    }

    result = inspect_jwt(decoded, required_role="admin")

    assert result["status"] == "FORBIDDEN"
    assert result["reason"] == "ROLE_NOT_AUTHORIZED"


def test_jwt_inspector_rejects_expired_token():

    decoded = {
        "payload": {
            "sub": "james",
            "role": "provider",
            "exp": 1600000000,
        }
    }

    result = inspect_jwt(decoded, required_role="provider")

    assert result["status"] == "UNTRUSTED"
    assert result["reason"] == "TOKEN_EXPIRED"