import logging
import uuid

import pytest


logger = logging.getLogger(__name__)

pytestmark = pytest.mark.regression


@pytest.mark.smoke
def test_create_valid_lab_order_returns_201(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="AUTO",
        synthetic_patient_id="SYN-PAT-AUTO-1001",
        test_code="CBC",
        priority="ROUTINE",
        ordered_at="2026-07-15T18:00:00Z",
    )

    response = lab_orders_client.create_order(request_body)

    assert response.status_code == 201

    response_body = response.json()

    assert (
        response_body["placer_order_number"]
        == request_body["placer_order_number"]
    )
    assert (
        response_body["synthetic_patient_id"]
        == request_body["synthetic_patient_id"]
    )
    assert response_body["test_code"] == request_body["test_code"]
    assert response_body["priority"] == request_body["priority"]
    assert response_body["status"] == "PLACED"
    assert "id" in response_body
    assert "created_at" in response_body


@pytest.mark.smoke
def test_created_lab_order_can_be_retrieved_by_id(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="RETRIEVE",
        synthetic_patient_id="SYN-PAT-AUTO-2001",
        test_code="CMP",
        priority="STAT",
        ordered_at="2026-07-15T19:00:00Z",
    )

    create_response = lab_orders_client.create_order(request_body)

    assert create_response.status_code == 201

    created_order = create_response.json()
    order_id = created_order["id"]

    retrieve_response = lab_orders_client.get_order(order_id)

    assert retrieve_response.status_code == 200

    retrieved_order = retrieve_response.json()

    assert retrieved_order["id"] == created_order["id"]
    assert (
        retrieved_order["placer_order_number"]
        == created_order["placer_order_number"]
    )
    assert (
        retrieved_order["synthetic_patient_id"]
        == created_order["synthetic_patient_id"]
    )
    assert retrieved_order["test_code"] == created_order["test_code"]
    assert retrieved_order["priority"] == created_order["priority"]
    assert retrieved_order["status"] == created_order["status"]
    assert retrieved_order["ordered_at"] == created_order["ordered_at"]
    assert retrieved_order["created_at"] == created_order["created_at"]


@pytest.mark.negative
def test_duplicate_placer_order_number_returns_409(
    lab_orders_client,
    lab_order_payload,
):
    original_request = lab_order_payload(
        prefix="DUPLICATE",
        synthetic_patient_id="SYN-PAT-ORIGINAL",
        test_code="CBC",
        priority="ROUTINE",
        ordered_at="2026-07-15T20:00:00Z",
    )

    duplicate_request = original_request.copy()
    duplicate_request.update(
        {
            "synthetic_patient_id": "SYN-PAT-DUPLICATE",
            "test_code": "TSH",
            "priority": "STAT",
            "ordered_at": "2026-07-15T20:30:00Z",
        }
    )

    original_response = lab_orders_client.create_order(original_request)

    assert original_response.status_code == 201

    duplicate_response = lab_orders_client.create_order(
        duplicate_request
    )

    assert duplicate_response.status_code == 409
    assert duplicate_response.json()["detail"] == (
        "placer_order_number already exists"
    )

    original_order = original_response.json()
    retrieve_response = lab_orders_client.get_order(
        original_order["id"]
    )

    assert retrieve_response.status_code == 200

    stored_order = retrieve_response.json()

    assert (
        stored_order["placer_order_number"]
        == original_request["placer_order_number"]
    )
    assert (
        stored_order["synthetic_patient_id"]
        == original_request["synthetic_patient_id"]
    )
    assert stored_order["test_code"] == original_request["test_code"]
    assert stored_order["priority"] == original_request["priority"]


@pytest.mark.negative
def test_invalid_priority_returns_422(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="INVALID-PRIORITY",
        synthetic_patient_id="SYN-PAT-AUTO-3001",
        test_code="CBC",
        priority="URGENT",
        ordered_at="2026-07-15T21:00:00Z",
    )

    assert request_body["priority"] == "URGENT"

    response = lab_orders_client.create_order(request_body)

    assert response.status_code == 422

    response_body = response.json()
    error = response_body["detail"][0]

    assert error["loc"] == ["body", "priority"]
    assert error["type"] == "enum"
    assert error["input"] == request_body["priority"]


@pytest.mark.negative
def test_missing_test_code_returns_422(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="MISSING-CODE",
        synthetic_patient_id="SYN-PAT-AUTO-4001",
        priority="ROUTINE",
        ordered_at="2026-07-15T22:00:00Z",
        include_test_code=False,
    )

    assert "test_code" not in request_body

    response = lab_orders_client.create_order(request_body)

    assert response.status_code == 422

    response_body = response.json()
    error = response_body["detail"][0]

    assert error["loc"] == ["body", "test_code"]
    assert error["type"] == "missing"
    assert error["msg"] == "Field required"


def test_missing_priority_defaults_to_routine(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="DEFAULT-PRIORITY",
        synthetic_patient_id="SYN-PAT-AUTO-5001",
        test_code="LIPID",
        ordered_at="2026-07-15T23:00:00Z",
        include_priority=False,
    )

    assert "priority" not in request_body

    response = lab_orders_client.create_order(request_body)

    assert response.status_code == 201

    response_body = response.json()

    assert response_body["priority"] == "ROUTINE"
    assert response_body["status"] == "PLACED"
    assert (
        response_body["placer_order_number"]
        == request_body["placer_order_number"]
    )


@pytest.mark.parametrize(
    (
        "test_code",
        "expected_status",
        "expected_error_type",
    ),
    [
        pytest.param(
            "",
            422,
            "string_too_short",
            marks=pytest.mark.negative,
            id="zero-characters-invalid",
        ),
        pytest.param(
            "X",
            201,
            None,
            id="one-character-valid",
        ),
        pytest.param(
            "X" * 30,
            201,
            None,
            id="thirty-characters-valid",
        ),
        pytest.param(
            "X" * 31,
            422,
            "string_too_long",
            marks=pytest.mark.negative,
            id="thirty-one-characters-invalid",
        ),
    ],
)
def test_test_code_length_boundaries(
    lab_orders_client,
    lab_order_payload,
    test_code,
    expected_status,
    expected_error_type,
):
    request_body = lab_order_payload(
        prefix="CODE-BOUNDARY",
        synthetic_patient_id="SYN-PAT-BOUNDARY",
        test_code=test_code,
        priority="ROUTINE",
        ordered_at="2026-07-15T23:30:00Z",
    )

    logger.info(
        "Starting boundary test: "
        "test_code=%r, length=%d, expected_status=%d, "
        "expected_error_type=%r",
        test_code,
        len(test_code),
        expected_status,
        expected_error_type,
    )

    logger.info(
        "Request data: placer_order_number=%s, "
        "synthetic_patient_id=%s, priority=%s",
        request_body["placer_order_number"],
        request_body["synthetic_patient_id"],
        request_body["priority"],
    )

    response = lab_orders_client.create_order(request_body)

    logger.info(
        "Actual response: status=%d, body=%s",
        response.status_code,
        response.text,
    )

    assert request_body["test_code"] == test_code
    assert len(request_body["test_code"]) == len(test_code)
    assert response.status_code == expected_status

    response_body = response.json()

    if expected_status == 201:
        logger.info(
            "Valid boundary accepted: test_code=%r, length=%d",
            response_body["test_code"],
            len(response_body["test_code"]),
        )

        assert response_body["test_code"] == test_code
        assert response_body["status"] == "PLACED"
    else:
        error = response_body["detail"][0]

        logger.info(
            "Invalid boundary rejected: location=%s, "
            "error_type=%s, message=%s",
            error["loc"],
            error["type"],
            error["msg"],
        )

        assert error["loc"] == ["body", "test_code"]
        assert error["type"] == expected_error_type


@pytest.mark.negative
def test_malformed_order_id_returns_422(
    lab_orders_client,
):
    malformed_order_id = "not-a-valid-uuid"

    logger.info(
        "Retrieving order with malformed UUID: order_id=%r",
        malformed_order_id,
    )

    response = lab_orders_client.get_order(malformed_order_id)

    logger.info(
        "Malformed UUID response: status=%d body=%s",
        response.status_code,
        response.text,
    )

    assert response.status_code == 422

    response_body = response.json()
    error = response_body["detail"][0]

    assert error["loc"] == ["path", "order_id"]
    assert error["type"] == "uuid_parsing"
    assert error["input"] == malformed_order_id


@pytest.mark.negative
def test_nonexistent_order_id_returns_404(
    lab_orders_client,
):
    nonexistent_order_id = (
        "11111111-1111-1111-1111-111111111111"
    )

    logger.info(
        "Retrieving nonexistent order: order_id=%s",
        nonexistent_order_id,
    )

    response = lab_orders_client.get_order(nonexistent_order_id)

    logger.info(
        "Nonexistent UUID response: status=%d body=%s",
        response.status_code,
        response.text,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == (
        "laboratory order not found"
    )


@pytest.mark.negative
def test_malformed_ordered_at_returns_422(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="INVALID-DATETIME",
        synthetic_patient_id="SYN-PAT-AUTO-6001",
        test_code="TSH",
        priority="ROUTINE",
        ordered_at="tomorrow around lunchtime",
    )

    assert (
        request_body["ordered_at"]
        == "tomorrow around lunchtime"
    )

    logger.info(
        "Sending malformed datetime: "
        "placer_order_number=%s, ordered_at=%r",
        request_body["placer_order_number"],
        request_body["ordered_at"],
    )

    response = lab_orders_client.create_order(request_body)

    logger.info(
        "Malformed datetime response: status=%d body=%s",
        response.status_code,
        response.text,
    )

    assert response.status_code == 422

    response_body = response.json()
    error = response_body["detail"][0]

    assert error["loc"] == ["body", "ordered_at"]
    assert error["type"] == "datetime_from_date_parsing"
    assert error["input"] == request_body["ordered_at"]


@pytest.mark.smoke
def test_create_lab_order_with_valid_clinical_context_returns_201(
    lab_orders_client,
    lab_order_payload,
    clinical_context,
):
    request_body = lab_order_payload(
        prefix="CLINICAL-CONTEXT",
        synthetic_patient_id=clinical_context[
            "synthetic_patient_id"
        ],
        patient_id=clinical_context["patient_id"],
        encounter_id=clinical_context["encounter_id"],
        test_code="CBC",
        priority="ROUTINE",
        ordered_at="2026-07-16T15:00:00Z",
    )

    response = lab_orders_client.create_order(request_body)

    assert response.status_code == 201

    response_body = response.json()

    assert (
        response_body["patient_id"]
        == str(clinical_context["patient_id"])
    )
    assert (
        response_body["encounter_id"]
        == str(clinical_context["encounter_id"])
    )
    assert (
        response_body["synthetic_patient_id"]
        == clinical_context["synthetic_patient_id"]
    )


@pytest.mark.negative
def test_patient_id_without_encounter_id_returns_422(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="PATIENT-ONLY",
        patient_id=uuid.uuid4(),
        test_code="CBC",
        priority="ROUTINE",
        ordered_at="2026-07-16T15:15:00Z",
    )

    assert "patient_id" in request_body
    assert "encounter_id" not in request_body

    response = lab_orders_client.create_order(request_body)

    assert response.status_code == 422

    error = response.json()["detail"][0]

    assert error["loc"] == ["body"]
    assert error["type"] == "value_error"
    assert (
        "patient_id and encounter_id must be provided together"
        in error["msg"]
    )


@pytest.mark.negative
def test_encounter_id_without_patient_id_returns_422(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="ENCOUNTER-ONLY",
        encounter_id=uuid.uuid4(),
        test_code="CBC",
        priority="ROUTINE",
        ordered_at="2026-07-16T15:30:00Z",
    )

    assert "patient_id" not in request_body
    assert "encounter_id" in request_body

    response = lab_orders_client.create_order(request_body)

    assert response.status_code == 422

    error = response.json()["detail"][0]

    assert error["loc"] == ["body"]
    assert error["type"] == "value_error"
    assert (
        "patient_id and encounter_id must be provided together"
        in error["msg"]
    )


@pytest.mark.negative
def test_unknown_clinical_context_returns_409(
    lab_orders_client,
    lab_order_payload,
):
    request_body = lab_order_payload(
        prefix="UNKNOWN-CONTEXT",
        patient_id=uuid.uuid4(),
        encounter_id=uuid.uuid4(),
        test_code="CBC",
        priority="ROUTINE",
        ordered_at="2026-07-16T15:45:00Z",
    )

    response = lab_orders_client.create_order(request_body)

    assert response.status_code == 409
    assert response.json()["detail"] == (
        "laboratory order conflicts with existing data"
    )