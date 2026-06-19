from framework.payloads.payload_engine import (
    inspect_payload,
    encode_json_as_base64_zlib,
)

import json
import base64


def test_plain_json_detection():

    transaction = {
        "transactionType": "PATIENT_CHECK_IN",
        "appointmentId": "APT001",
    }

    payload = json.dumps(transaction)

    result = inspect_payload(payload)

    assert "JSON" in result["detectedFormats"]
    assert result["decodedObject"]["appointmentId"] == "APT001"


def test_base64_json_detection():

    transaction = {
        "transactionType": "PATIENT_CHECK_IN",
        "appointmentId": "APT001",
    }

    json_payload = json.dumps(transaction)

    encoded = base64.b64encode(
        json_payload.encode("utf-8")
    ).decode("utf-8")

    result = inspect_payload(encoded)

    assert "BASE64" in result["detectedFormats"]
    assert "JSON" in result["detectedFormats"]


def test_base64_zlib_detection():

    transaction = {
        "transactionType": "PATIENT_CHECK_IN",
        "appointmentId": "APT001",
        "encounterId": "ENC000001",
    }

    payload = encode_json_as_base64_zlib(
        transaction
    )

    result = inspect_payload(payload)

    assert "BASE64" in result["detectedFormats"]
    assert "ZLIB_COMPRESSED" in result["detectedFormats"]
    assert "JSON" in result["detectedFormats"]


def test_jwt_detection():

    payload = "header.payload.signature"

    result = inspect_payload(payload)

    assert "JWT_LIKE" in result["detectedFormats"]


def test_unknown_payload():

    payload = "not-a-valid-payload"

    result = inspect_payload(payload)

    assert result["notes"] != []

def test_rosetta_trace_mode_prints_detection_steps():

    transaction = {
        "transactionType": "PATIENT_CHECK_IN",
        "appointmentId": "APT001",
        "encounterId": "ENC000001",
    }

    payload = encode_json_as_base64_zlib(transaction)

    result = inspect_payload(payload, trace=True)

    assert "BASE64" in result["detectedFormats"]
    assert "ZLIB_COMPRESSED" in result["detectedFormats"]
    assert "JSON" in result["detectedFormats"]