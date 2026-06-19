import base64
import json
import zlib


def inspect_payload(payload: str, trace: bool = False) -> dict:
    result = {
        "originalPayload": payload,
        "detectedFormats": [],
        "decodedText": None,
        "decodedObject": None,
        "notes": [],
    }

    if trace:
        _trace_header()
        print("STEP 1: Payload received")
        print(payload)

    if _looks_like_json(payload):
        if trace:
            print("\nSTEP 2: Plain JSON detected")

        result["detectedFormats"].append("JSON")
        result["decodedText"] = payload
        result["decodedObject"] = json.loads(payload)
        result["notes"].append("Payload appears to be plain JSON.")
        return result

    if _looks_like_jwt(payload):
        if trace:
            print("\nSTEP 2: JWT-like structure detected")
            print("Reason: payload contains three dot-separated sections.")

        result["detectedFormats"].append("JWT_LIKE")
        result["notes"].append("Payload looks like a JWT-style token.")
        return result

    if trace:
        print("\nSTEP 2: Attempting Base64 decode")

    decoded_bytes = _try_base64_decode(payload)

    if decoded_bytes is None:
        if trace:
            print("Base64 decode failed.")
            print("Result: unknown or unsupported payload format.")
            _trace_footer()

        result["notes"].append("Payload is not valid JSON, JWT-like, or Base64.")
        return result

    result["detectedFormats"].append("BASE64")

    if trace:
        print("Base64 decode successful.")
        print(f"Decoded byte length: {len(decoded_bytes)}")

    if trace:
        print("\nSTEP 3: Attempting zlib decompression")

    decompressed_bytes = _try_zlib_decompress(decoded_bytes)

    if decompressed_bytes is not None:
        result["detectedFormats"].append("ZLIB_COMPRESSED")

        decoded_text = decompressed_bytes.decode("utf-8")
        result["decodedText"] = decoded_text

        if trace:
            print("zlib decompression successful.")
            print(f"Decompressed byte length: {len(decompressed_bytes)}")
            print("\nSTEP 4: Decoded text after decompression")
            print(decoded_text)

        if _looks_like_json(decoded_text):
            result["detectedFormats"].append("JSON")
            result["decodedObject"] = json.loads(decoded_text)

            if trace:
                print("\nSTEP 5: JSON detected after decompression")
                print("Payload successfully reconstructed into a business object.")

        result["notes"].append("Payload was Base64 decoded and zlib decompressed.")

        if trace:
            _trace_footer()

        return result

    if trace:
        print("zlib decompression failed.")
        print("\nSTEP 4: Attempting UTF-8 decode of Base64 bytes")

    try:
        decoded_text = decoded_bytes.decode("utf-8")
        result["decodedText"] = decoded_text

        if trace:
            print("UTF-8 decode successful.")
            print(decoded_text)

        if _looks_like_json(decoded_text):
            result["detectedFormats"].append("JSON")
            result["decodedObject"] = json.loads(decoded_text)

            if trace:
                print("\nSTEP 5: JSON detected after Base64 decode")
                print("Payload successfully reconstructed into a business object.")

        result["notes"].append("Payload was Base64 decoded into UTF-8 text.")

        if trace:
            _trace_footer()

        return result

    except UnicodeDecodeError:
        if trace:
            print("UTF-8 decode failed.")
            print("Payload may be binary, encrypted, or unsupported.")
            _trace_footer()

        result["notes"].append("Payload was Base64 decoded but is not readable UTF-8.")
        return result


def encode_json_as_base64_zlib(data: dict) -> str:
    json_text = json.dumps(data, separators=(",", ":"))
    utf8_bytes = json_text.encode("utf-8")
    compressed_bytes = zlib.compress(utf8_bytes)

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


def _trace_header() -> None:
    print("\n========================================")
    print("PAYLOAD ROSETTA TRACE")
    print("========================================")


def _trace_footer() -> None:
    print("========================================\n")