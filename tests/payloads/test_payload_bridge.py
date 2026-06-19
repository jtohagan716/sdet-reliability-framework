from framework.payloads.payload_bridge import (
    bridge_replace_payload_values,
)

from framework.payloads.payload_engine import (
    encode_json_as_base64_zlib,
)


def sample_payload():

    transaction = {
        "transactionType": "PATIENT_CHECK_IN",
        "facilityNcid": "1048021",
        "appointmentId": "APT001",
        "encounterId": "ENC000001",
        "patientId": "PAT12345",
        "sessionId": "SESSION001",
        "timestamp": "2026-06-19T09:00:00",
    }

    return encode_json_as_base64_zlib(
        transaction
    )


def test_bridge_replaces_values():

    result = bridge_replace_payload_values(
        sample_payload(),
        {
            "appointmentId": "APT999",
            "encounterId": "ENC999999",
            "sessionId": "SESSION999",
        },
    )

    assert (
        result["updatedObject"]["appointmentId"]
        == "APT999"
    )

    assert (
        result["updatedObject"]["encounterId"]
        == "ENC999999"
    )

    assert (
        result["updatedObject"]["sessionId"]
        == "SESSION999"
    )


def test_bridge_rebuilds_payload():

    result = bridge_replace_payload_values(
        sample_payload(),
        {
            "encounterId": "ENC777777",
        },
    )

    assert result["rebuiltPayload"] is not None

    assert result["integrityVerified"] is True


def test_bridge_preserves_static_fields():

    result = bridge_replace_payload_values(
        sample_payload(),
        {
            "sessionId": "NEWSESSION",
        },
    )

    assert (
        result["updatedObject"]["transactionType"]
        == "PATIENT_CHECK_IN"
    )

    assert (
        result["updatedObject"]["facilityNcid"]
        == "1048021"
    )

def test_bridge_trace_mode_prints_payload_journey():

    result = bridge_replace_payload_values(
        sample_payload(),
        {
            "appointmentId": "APT999",
            "encounterId": "ENC999999",
            "sessionId": "SESSION999",
        },
        trace=True,
    )

    assert result["integrityVerified"] is True