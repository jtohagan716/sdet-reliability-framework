from framework.fhir.transaction_reporter import generate_transaction_report


def test_transaction_demo():

    transaction = {
        "transactionType": "PATIENT_CHECK_IN",
        "facilityNcid": "1048021",
        "appointmentId": "APT001",
        "encounterId": "ENC000001",
        "userId": "RECEPTION01",
        "workstationId": "CLINIC-WS-05",
        "timestamp": "2026-06-18T09:00:00",
    }

    report = generate_transaction_report(transaction)

    print()
    print(report)

    assert "HEALTHCARE TRANSACTION INSPECTION REPORT" in report