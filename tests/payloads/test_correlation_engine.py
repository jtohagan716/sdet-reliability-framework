from framework.payloads.correlation_engine import (
    analyze_transaction_fields,
    generate_correlation_report,
)


def sample_transaction():
    return {
        "transactionType": "PATIENT_CHECK_IN",
        "workflow": "RECEPTION_CHECK_IN",
        "facilityNcid": "1048021",
        "sessionId": "SESSION001",
        "appointmentId": "APT001",
        "encounterId": "ENC000001",
        "patientId": "PAT12345",
        "timestamp": "2026-06-18T09:00:00",
        "workstationId": "CLINIC-WS-05",
    }


def test_correlation_engine_identifies_dynamic_fields():

    result = analyze_transaction_fields(sample_transaction())

    assert "sessionId" in result["dynamicFields"]
    assert "appointmentId" in result["dynamicFields"]
    assert "encounterId" in result["dynamicFields"]
    assert "timestamp" in result["dynamicFields"]


def test_correlation_engine_identifies_static_fields():

    result = analyze_transaction_fields(sample_transaction())

    assert "transactionType" in result["staticFields"]
    assert "workflow" in result["staticFields"]
    assert "facilityNcid" in result["staticFields"]


def test_correlation_engine_identifies_unknown_fields():

    result = analyze_transaction_fields(sample_transaction())

    assert "workstationId" in result["unknownFields"]


def test_correlation_candidates_match_dynamic_fields():

    result = analyze_transaction_fields(sample_transaction())

    assert result["correlationCandidates"] == result["dynamicFields"]


def test_correlation_report_contains_expected_sections():

    report = generate_correlation_report(sample_transaction())

    assert "ENTERPRISE TRANSACTION CORRELATION REPORT" in report
    assert "STATIC FIELDS" in report
    assert "DYNAMIC FIELDS" in report
    assert "CORRELATION CANDIDATES" in report
    assert "Replay Safe" in report