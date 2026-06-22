from framework.security.jwt_decoder import (
    is_token_expired,
    has_role,
    has_trusted_issuer,
)


def inspect_jwt(
    decoded_token: dict,
    required_role: str,
    trusted_issuer: str,
) -> dict:
    expired = is_token_expired(decoded_token)
    issuer_trusted = has_trusted_issuer(
        decoded_token,
        trusted_issuer,
    )
    role_allowed = has_role(decoded_token, required_role)

    if expired:
        status = "UNTRUSTED"
        reason = "TOKEN_EXPIRED"
    elif not issuer_trusted:
        status = "UNTRUSTED"
        reason = "UNTRUSTED_ISSUER"
    elif not role_allowed:
        status = "FORBIDDEN"
        reason = "ROLE_NOT_AUTHORIZED"
    else:
        status = "TRUSTED"
        reason = "ACCESS_GRANTED"

    return {
        "subject": decoded_token["payload"].get("sub"),
        "role": decoded_token["payload"].get("role"),
        "issuer": decoded_token["payload"].get("iss"),
        "requiredRole": required_role,
        "trustedIssuer": trusted_issuer,
        "expired": expired,
        "issuerTrusted": issuer_trusted,
        "roleAllowed": role_allowed,
        "status": status,
        "reason": reason,
    }


def print_jwt_security_report(result: dict) -> None:
    print("")
    print("================================")
    print("JWT SECURITY REPORT")
    print("================================")
    print(f"Subject        : {result['subject']}")
    print(f"Role           : {result['role']}")
    print(f"Issuer         : {result['issuer']}")
    print(f"Required Role  : {result['requiredRole']}")
    print(f"Trusted Issuer : {result['trustedIssuer']}")
    print(f"Expired        : {result['expired']}")
    print(f"Issuer Trusted : {result['issuerTrusted']}")
    print(f"Role Allowed   : {result['roleAllowed']}")
    print(f"Status         : {result['status']}")
    print(f"Reason         : {result['reason']}")
    print("================================")
    print("")