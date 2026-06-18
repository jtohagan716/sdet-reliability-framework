from framework.fhir.transaction_reporter import generate_transaction_report


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


def test_transaction_report_contains_header():

    report = generate_transaction_report(valid_checkin_transaction())

    assert "HEALTHCARE TRANSACTION INSPECTION REPORT" in report


def test_transaction_report_contains_business_fields():

    report = generate_transaction_report(valid_checkin_transaction())

    assert "PATIENT_CHECK_IN" in report
    assert "1048021" in report
    assert "APT001" in report
    assert "ENC000001" in report
    assert "RECEPTION01" in report


def test_transaction_report_contains_payload_metrics():

    report = generate_transaction_report(valid_checkin_transaction())

    assert "UTF-8 Size" in report
    assert "Compressed Size" in report
    assert "Base64 Size" in report
    assert "Compression Savings" in report
    assert "Base64 Overhead" in report
    assert "Net Savings" in report


def test_transaction_report_contains_transport_payload():

    report = generate_transaction_report(valid_checkin_transaction())

    assert "TRANSPORT PAYLOAD" in report