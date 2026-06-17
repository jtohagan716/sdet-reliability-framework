from framework.fhir.appointment_workflow import check_in_appointment


def test_booked_appointment_can_be_checked_in():

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

    result = check_in_appointment(appointment)

    assert result["valid"] is True
    assert result["appointment"]["status"] == "checked-in"


def test_arrived_appointment_can_be_checked_in():

    appointment = {
        "resourceType": "Appointment",
        "id": "appt001",
        "status": "arrived",
        "participant": [
            {
                "actor": {
                    "reference": "Patient/12345",
                }
            }
        ],
    }

    result = check_in_appointment(appointment)

    assert result["valid"] is True
    assert result["appointment"]["status"] == "checked-in"


def test_cancelled_appointment_cannot_be_checked_in():

    appointment = {
        "resourceType": "Appointment",
        "id": "appt001",
        "status": "cancelled",
        "participant": [
            {
                "actor": {
                    "reference": "Patient/12345",
                }
            }
        ],
    }

    result = check_in_appointment(appointment)

    assert result["valid"] is False
    assert "cannot be checked in" in result["errors"][0]


def test_noshow_appointment_cannot_be_checked_in():

    appointment = {
        "resourceType": "Appointment",
        "id": "appt001",
        "status": "noshow",
        "participant": [
            {
                "actor": {
                    "reference": "Patient/12345",
                }
            }
        ],
    }

    result = check_in_appointment(appointment)

    assert result["valid"] is False
    assert "cannot be checked in" in result["errors"][0]