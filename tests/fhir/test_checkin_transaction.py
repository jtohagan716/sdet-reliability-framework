from framework.fhir.checkin_transaction import process_checkin_transaction
from framework.fhir.sequence_generator import SequenceGenerator


def valid_appointment():
    return {
        "resourceType": "Appointment",
        "id": "APT001",
        "status": "booked",
        "participant": [
            {
                "actor": {
                    "reference": "Patient/12345",
                }
            }
        ],
    }


def test_checkin_transaction_generates_encounter_id():

    encounter_sequence = SequenceGenerator(prefix="ENC", start=1)

    result = process_checkin_transaction(
        valid_appointment(),
        encounter_sequence,
    )

    assert result["success"] is True
    assert result["appointmentId"] == "APT001"
    assert result["appointmentStatus"] == "checked-in"
    assert result["encounterId"] == "ENC000001"
    assert result["encounterStatus"] == "in-progress"
    assert result["errors"] == []


def test_checkin_transaction_increments_encounter_id():

    encounter_sequence = SequenceGenerator(prefix="ENC", start=1)

    first_result = process_checkin_transaction(
        valid_appointment(),
        encounter_sequence,
    )

    second_result = process_checkin_transaction(
        valid_appointment(),
        encounter_sequence,
    )

    assert first_result["encounterId"] == "ENC000001"
    assert second_result["encounterId"] == "ENC000002"


def test_checkin_transaction_requires_appointment_id():

    appointment = valid_appointment()
    appointment.pop("id")

    encounter_sequence = SequenceGenerator(prefix="ENC", start=1)

    result = process_checkin_transaction(
        appointment,
        encounter_sequence,
    )

    assert result["success"] is False
    assert "appointment id is required" in result["errors"]


def test_checkin_transaction_rejects_cancelled_appointment():

    appointment = valid_appointment()
    appointment["status"] = "cancelled"

    encounter_sequence = SequenceGenerator(prefix="ENC", start=1)

    result = process_checkin_transaction(
        appointment,
        encounter_sequence,
    )

    assert result["success"] is False
    assert "appointment is not eligible for check-in transaction" in result["errors"]