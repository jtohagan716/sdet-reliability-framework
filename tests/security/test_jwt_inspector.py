from framework.security.jwt_decoder import decode_jwt
from framework.security.jwt_inspector import (
    inspect_jwt,
    print_jwt_security_report,
)


TRUSTED_ISSUER = "https://company-login.com"


def test_jwt_inspector_trusts_valid_provider_token():

    decoded = {
        "payload": {
            "sub": "james",
            "role": "provider",
            "iss": TRUSTED_ISSUER,
            "exp": 1890000000,
        }
    }

    result = inspect_jwt(
        decoded,
        required_role="provider",
        trusted_issuer=TRUSTED_ISSUER,
    )

    print_jwt_security_report(result)

    assert result["status"] == "TRUSTED"
    assert result["reason"] == "ACCESS_GRANTED"


def test_jwt_inspector_forbids_wrong_role():

    decoded = {
        "payload": {
            "sub": "james",
            "role": "provider",
            "iss": TRUSTED_ISSUER,
            "exp": 1890000000,
        }
    }

    result = inspect_jwt(
        decoded,
        required_role="admin",
        trusted_issuer=TRUSTED_ISSUER,
    )

    assert result["status"] == "FORBIDDEN"
    assert result["reason"] == "ROLE_NOT_AUTHORIZED"


def test_jwt_inspector_rejects_expired_token():

    decoded = {
        "payload": {
            "sub": "james",
            "role": "provider",
            "iss": TRUSTED_ISSUER,
            "exp": 1600000000,
        }
    }

    result = inspect_jwt(
        decoded,
        required_role="provider",
        trusted_issuer=TRUSTED_ISSUER,
    )

    assert result["status"] == "UNTRUSTED"
    assert result["reason"] == "TOKEN_EXPIRED"


def test_jwt_inspector_rejects_untrusted_issuer():

    decoded = {
        "payload": {
            "sub": "james",
            "role": "provider",
            "iss": "https://evil-site.com",
            "exp": 1890000000,
        }
    }

    result = inspect_jwt(
        decoded,
        required_role="provider",
        trusted_issuer=TRUSTED_ISSUER,
    )

    assert result["status"] == "UNTRUSTED"
    assert result["reason"] == "UNTRUSTED_ISSUER"