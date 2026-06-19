import json

from framework.payloads.payload_rosetta import (
    encode_json_as_base64_zlib,
    inspect_payload,
)


def decode_payload_to_object(payload: str) -> dict:
    inspection = inspect_payload(payload)

    if inspection["decodedObject"] is None:
        raise ValueError("Unable to decode payload into a structured object.")

    return inspection["decodedObject"]


def update_payload_fields(payload_object: dict, replacements: dict) -> dict:
    updated = payload_object.copy()

    for key, value in replacements.items():
        if key in updated:
            updated[key] = value

    return updated


def encode_object_to_payload(payload_object: dict) -> str:
    return encode_json_as_base64_zlib(payload_object)


def pretty_print_payload_object(payload_object: dict) -> str:
    return json.dumps(payload_object, indent=4)


def verify_round_trip(original_payload: str) -> bool:
    original_object = decode_payload_to_object(original_payload)
    rebuilt_payload = encode_object_to_payload(original_object)
    rebuilt_object = decode_payload_to_object(rebuilt_payload)

    return original_object == rebuilt_object