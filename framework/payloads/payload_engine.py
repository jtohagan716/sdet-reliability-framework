import json

from framework.payloads.payload_rosetta import (
    encode_json_as_base64_zlib,
    inspect_payload,
)


def decode_payload_to_object(payload: str, trace: bool = False) -> dict:
    if trace:
        print("\nSTEP A: Payload Engine requested decode")

    inspection = inspect_payload(payload, trace=trace)

    if inspection["decodedObject"] is None:
        raise ValueError("Unable to decode payload into a structured object.")

    if trace:
        print("\nSTEP B: Payload Engine received structured object")
        print(inspection["decodedObject"])

    return inspection["decodedObject"]


def update_payload_fields(
    payload_object: dict,
    replacements: dict,
    trace: bool = False,
) -> dict:
    updated = payload_object.copy()

    if trace:
        print("\nSTEP C: Payload Engine preparing field replacements")
        print("Original object:")
        print(payload_object)
        print("Requested replacements:")
        print(replacements)

    for key, value in replacements.items():
        if key in updated:
            if trace:
                print(f"Replacing {key}: {updated[key]} -> {value}")

            updated[key] = value
        else:
            if trace:
                print(f"Skipping {key}: field not present in payload object")

    if trace:
        print("\nSTEP D: Payload Engine updated object")
        print(updated)

    return updated


def encode_object_to_payload(
    payload_object: dict,
    trace: bool = False,
) -> str:
    if trace:
        print("\nSTEP E: Payload Engine rebuilding transport-safe payload")
        print("Object being encoded:")
        print(payload_object)

    rebuilt_payload = encode_json_as_base64_zlib(payload_object)

    if trace:
        print("\nSTEP F: Payload Engine rebuilt payload")
        print(rebuilt_payload)

    return rebuilt_payload


def pretty_print_payload_object(payload_object: dict) -> str:
    return json.dumps(payload_object, indent=4)


def verify_round_trip(original_payload: str, trace: bool = False) -> bool:
    if trace:
        print("\nSTEP G: Payload Engine verifying round trip")

    original_object = decode_payload_to_object(original_payload, trace=trace)
    rebuilt_payload = encode_object_to_payload(original_object, trace=trace)
    rebuilt_object = decode_payload_to_object(rebuilt_payload, trace=trace)

    verified = original_object == rebuilt_object

    if trace:
        print("\nSTEP H: Round trip verification result")
        print(verified)

    return verified