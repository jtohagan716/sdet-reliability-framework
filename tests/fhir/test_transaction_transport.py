from framework.fhir.transaction_transport import transport_transaction


def valid_checkin_transaction():
    return {
        "transactionType": "PATIENT_CHECK_IN",
        "facilityNcid": "1048021",
        "appointmentId": "APT001",
        "encounterId": "ENC000001",
        "userId": "RECEPTION01",
        "workstationId": "CLINIC-WS-05",
        "sessionId": "SESSION001",
        "timestamp": "2026-06-18T09:00:00",
    }


def test_transport_transaction_succeeds():

    result = transport_transaction(valid_checkin_transaction())

    assert result["transportStatus"] == "SUCCESS"
    assert result["integrityVerified"] is True


def test_transport_transaction_preserves_original_transaction():

    transaction = valid_checkin_transaction()

    result = transport_transaction(transaction)

    assert result["receivedTransaction"] == transaction


def test_transport_transaction_returns_encoded_payload():

    result = transport_transaction(valid_checkin_transaction())

    assert result["transportPayload"] is not None
    assert isinstance(result["transportPayload"], str)


def test_transport_transaction_returns_transport_metrics():

    result = transport_transaction(valid_checkin_transaction())

    assert result["transportMetrics"]["utf8SizeBytes"] > 0
    assert result["transportMetrics"]["compressedSizeBytes"] > 0
    assert result["transportMetrics"]["base64SizeBytes"] > 0
    assert result["transportMetrics"]["recommendation"] is not None
    