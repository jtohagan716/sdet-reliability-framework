from framework.fhir.transaction_inspector import (
    decode_transaction_payload,
    inspect_transaction,
)


def transport_transaction(transaction: dict) -> dict:
    inspection = inspect_transaction(transaction)

    received_transaction = decode_transaction_payload(
        inspection["base64_payload"]
    )

    integrity_verified = received_transaction == transaction

    return {
        "transportStatus": "SUCCESS" if integrity_verified else "FAILED",
        "originalTransaction": transaction,
        "transportPayload": inspection["base64_payload"],
        "receivedTransaction": received_transaction,
        "integrityVerified": integrity_verified,
        "transportMetrics": {
            "utf8SizeBytes": inspection["utf8_size_bytes"],
            "compressedSizeBytes": inspection["compressed_size_bytes"],
            "base64SizeBytes": inspection["base64_size_bytes"],
            "compressionSavingsPercent": inspection["compression_savings_percent"],
            "base64OverheadPercent": inspection["transport_overhead_percent"],
            "netSavingsPercent": inspection["net_savings_percent"],
            "recommendation": inspection["recommendation"],
        },
    }