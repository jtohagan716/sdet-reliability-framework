import base64
import json
import zlib


def inspect_payload(payload: str) -> dict:
    result = {
        "originalPayload": payload,
        "detectedFormats": [],
        "decodedText": None,
        "decodedObject": None,
        "notes": [],
    }

    if _looks_like_json(payload):
        result["detectedFormats"].append("JSON")
        result["decodedText"] = payload
        result["decodedObject"] = json.loads(payload)
        result["notes"].append("Payload appears to be plain JSON.")
        return result

    if _looks_like_jwt(payload):
        result["detectedFormats"].append("JWT_LIKE")
        result["notes"].append("Payload looks like a JWT-style token.")
        return result
    
    decoded_bytes = _try_base64_decode(payload)

    if decoded_bytes is None:
        result["notes"].append("Payload is not valid JSON or Base64.")
        return result

    result["detectedFormats"].append("BASE64")

    decompressed_bytes = _try_zlib_decompress(decoded_bytes)

    if decompressed_bytes is not None:
        result["detectedFormats"].append("ZLIB_COMPRESSED")
        decoded_text = decompressed_bytes.decode("utf-8")
    else:
        decoded_text = decoded_bytes.decode("utf-8")

    result["decodedText"] = decoded_text

    if _looks_like_json(decoded_text):
        result["detectedFormats"].append("JSON")
        result["decodedObject"] = json.loads(decoded_text)

    return result


def encode_json_as_base64_zlib(data: dict) -> str:
    json_text = json.dumps(data, separators=(",", ":"))
    compressed_bytes = zlib.compress(json_text.encode("utf-8"))
    return base64.b64encode(compressed_bytes).decode("utf-8")


def _looks_like_json(payload: str) -> bool:
    try:
        json.loads(payload)
        return True
    except json.JSONDecodeError:
        return False
    
def _looks_like_jwt(payload: str) -> bool:
    parts = payload.split(".")
    return len(parts) == 3 and all(parts)

def _try_base64_decode(payload: str) -> bytes | None:
    try:
        return base64.b64decode(payload, validate=True)
    except Exception:
        return None


def _try_zlib_decompress(payload_bytes: bytes) -> bytes | None:
    try:
        return zlib.decompress(payload_bytes)
    except zlib.error:
        return None