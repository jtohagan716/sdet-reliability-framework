import base64
import json
from datetime import datetime, UTC


def decode_jwt(token: str) -> dict:
    header_b64, payload_b64, signature = token.split(".")

    def decode_section(section: str) -> dict:
        padding = "=" * (-len(section) % 4)
        decoded_bytes = base64.urlsafe_b64decode(section + padding)
        decoded_text = decoded_bytes.decode("utf-8")
        return json.loads(decoded_text)

    return {
        "header": decode_section(header_b64),
        "payload": decode_section(payload_b64),
        "signature": signature,
    }


def print_jwt_trace(decoded_token: dict) -> None:
    print("")
    print("================================")
    print("JWT TRACE")
    print("================================")

    print("Header:")
    print(json.dumps(decoded_token["header"], indent=2))

    print("")
    print("Payload / Claims:")
    print(json.dumps(decoded_token["payload"], indent=2))

    print("")
    print(f"Signature: {decoded_token['signature']}")

    print("================================")
    print("")


def is_token_expired(decoded_token: dict) -> bool:
    expiration = decoded_token["payload"].get("exp")

    if expiration is None:
        return True

    current_timestamp = int(datetime.now(UTC).timestamp())

    return current_timestamp > expiration

def has_role(decoded_token: dict, required_role: str) -> bool:
    actual_role = decoded_token["payload"].get("role")

    return actual_role == required_role