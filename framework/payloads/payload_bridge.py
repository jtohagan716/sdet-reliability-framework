from framework.payloads.payload_engine import (
    decode_payload_to_object,
    encode_object_to_payload,
    update_payload_fields,
)


def bridge_replace_payload_values(
    captured_payload: str,
    replacements: dict,
    trace: bool = False,
) -> dict:
    if trace:
        print("\n========================================")
        print("PAYLOAD BRIDGE TRACE")
        print("========================================")
        print("STEP 1: Captured payload received")
        print(captured_payload)

    original_object = decode_payload_to_object(
        captured_payload,
        trace=trace,
    )

    if trace:
        print("\nSTEP 2: Payload decoded into business object")
        print(original_object)

    updated_object = update_payload_fields(
        original_object,
        replacements,
        trace=trace,
    )

    if trace:
        print("\nSTEP 3: Dynamic values replaced")
        print("Replacements:")
        print(replacements)
        print("Updated object:")
        print(updated_object)

    rebuilt_payload = encode_object_to_payload(
        updated_object,
        trace=trace,
    )

    if trace:
        print("\nSTEP 4: Updated object rebuilt into transport payload")
        print(rebuilt_payload)

    decoded_rebuilt_object = decode_payload_to_object(
        rebuilt_payload,
        trace=trace,
    )

    if trace:
        print("\nSTEP 5: Rebuilt payload decoded again for integrity verification")
        print(decoded_rebuilt_object)
        print("\nIntegrity Verified:")
        print(decoded_rebuilt_object == updated_object)
        print("========================================\n")

    return {
        "originalObject": original_object,
        "updatedObject": updated_object,
        "rebuiltPayload": rebuilt_payload,
        "decodedRebuiltObject": decoded_rebuilt_object,
        "integrityVerified": decoded_rebuilt_object == updated_object,
    }