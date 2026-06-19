from framework.payloads.payload_engine import (
    decode_payload_to_object,
    encode_object_to_payload,
    update_payload_fields,
)


def bridge_replace_payload_values(captured_payload: str, replacements: dict) -> dict:
    original_object = decode_payload_to_object(captured_payload)

    updated_object = update_payload_fields(
        original_object,
        replacements,
    )

    rebuilt_payload = encode_object_to_payload(updated_object)

    decoded_rebuilt_object = decode_payload_to_object(rebuilt_payload)

    return {
        "originalObject": original_object,
        "updatedObject": updated_object,
        "rebuiltPayload": rebuilt_payload,
        "decodedRebuiltObject": decoded_rebuilt_object,
        "integrityVerified": decoded_rebuilt_object == updated_object,
    }