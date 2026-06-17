from framework.fhir.appointment_validator import validate_appointment_resource


def test_valid_appointment():

    appointment = {
        "resourceType": "Appointment",
        "id": "appt001",
        "status": "booked",
        "participant": [
            {
                "actor": {
                    "reference": "Patient/12345",
                }
            }
        ],
    }

    result = validate_appointment_resource(appointment)

    assert result["valid"] is True
    assert result["errors"] == []


def test_appointment_requires_patient_participant():

    appointment = {
        "resourceType": "Appointment",
        "id": "appt001",
        "status": "booked",
        "participant": [
            {
                "actor": {
                    "reference": "Practitioner/567",
                }
            }
        ],
    }

    result = validate_appointment_resource(appointment)

    assert result["valid"] is False
    assert "Appointment patient participant is required" in result["errors"]


def test_appointment_rejects_invalid_status():

    appointment = {
        "resourceType": "Appointment",
        "id": "appt001",
        "status": "banana",
        "participant": [
            {
                "actor": {
                    "reference": "Patient/12345",
                }
            }
        ],
    }

    result = validate_appointment_resource(appointment)

    assert result["valid"] is False
    assert "status has invalid value" in result["errors"]