from framework.security.jwt_decoder import (
    decode_jwt,
    print_jwt_trace,
    is_token_expired,
    has_role,
)


def test_decode_jwt():

    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJqYW1lcyIsInJvbGUiOiJwcm92aWRlciIsImV4cCI6MTg5MDAwMDAwMH0."
        "fake_signature"
    )

    result = decode_jwt(token)

    assert result["header"]["alg"] == "HS256"
    assert result["payload"]["sub"] == "james"
    assert result["payload"]["role"] == "provider"
    assert result["payload"]["exp"] == 1890000000


def test_jwt_trace_prints_decoded_token():

    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJqYW1lcyIsInJvbGUiOiJwcm92aWRlciIsImV4cCI6MTg5MDAwMDAwMH0."
        "fake_signature"
    )

    result = decode_jwt(token)

    print_jwt_trace(result)

    assert result["payload"]["role"] == "provider"


def test_token_with_future_expiration_is_not_expired():

    token = (
        "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
        "eyJzdWIiOiJqYW1lcyIsInJvbGUiOiJwcm92aWRlciIsImV4cCI6MTg5MDAwMDAwMH0."
        "fake_signature"
    )

    result = decode_jwt(token)

    assert is_token_expired(result) is False


def test_token_with_missing_expiration_is_treated_as_expired():

    decoded_token = {
        "payload": {
            "sub": "james",
            "role": "provider",
        }
    }

    assert is_token_expired(decoded_token) is True


def test_provider_role_matches():

    decoded_token = {
        "payload": {
            "role": "provider"
        }
    }

    assert has_role(decoded_token, "provider") is True


def test_provider_role_does_not_match_admin():

    decoded_token = {
        "payload": {
            "role": "provider"
        }
    }

    assert has_role(decoded_token, "admin") is False