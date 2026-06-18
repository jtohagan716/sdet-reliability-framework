from framework.fhir.transaction_inspector import (
    decode_transaction_payload,
    inspect_transaction,
)


def valid_checkin_transaction():
    return {
        "transactionType": "PATIENT_CHECK_IN",
        "facilityNcid": "1048021",
        "appointmentId": "APT001",
        "encounterId": "ENC000001",
        "userId": "RECEPTION01",
        "workstationId": "CLINIC-WS-05",
        "timestamp": "2026-06-18T09:00:00",
    }


def test_transaction_inspector_returns_payload_details():

    result = inspect_transaction(valid_checkin_transaction())

    assert result["business_object"]["transactionType"] == "PATIENT_CHECK_IN"
    assert result["serialized_json"] is not None
    assert result["utf8_size_bytes"] > 0
    assert result["compressed_size_bytes"] > 0
    assert result["base64_payload"] is not None
    assert result["base64_size_bytes"] > 0


def test_transaction_payload_round_trip_decodes_original_transaction():

    transaction = valid_checkin_transaction()

    inspected = inspect_transaction(transaction)

    decoded = decode_transaction_payload(
        inspected["base64_payload"]
    )

    assert decoded == transaction


def test_base64_payload_is_larger_than_compressed_payload():

    result = inspect_transaction(valid_checkin_transaction())

    assert result["base64_size_bytes"] >= result["compressed_size_bytes"]


def test_inspector_reports_transport_overhead():

    result = inspect_transaction(valid_checkin_transaction())

    assert result["transport_overhead_percent"] >= 0

def test_inspector_returns_transport_recommendation():

    result = inspect_transaction(valid_checkin_transaction())

    assert "recommendation" in result
    assert result["recommendation"] is not None