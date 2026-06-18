from framework.fhir.patient_checkin import process_patient_checkin


def valid_patient():
    return {
        "resourceType": "Patient",
        "identifier": [{"system": "http://hospital.org", "value": "12345"}],
        "name": [{"family": "Doe", "given": ["Jane"]}],
        "gender": "female",
        "birthDate": "1980-01-01",
    }


def valid_appointment():
    return {
        "resourceType": "Appointment",
        "id": "appt001",
        "status": "checked-in",
        "participant": [{"actor": {"reference": "Patient/12345"}}],
    }


def valid_organization():
    return {
        "resourceType": "Organization",
        "id": "sjafb",
        "identifier": [{"system": "urn:ahlta:facility-ncid", "value": "1048021"}],
        "name": "Seymour Johnson MTF",
    }


def valid_location():
    return {
        "resourceType": "Location",
        "id": "clinic-room-5",
        "name": "Exam Room 5",
    }


def valid_practitioner():
    return {
        "resourceType": "Practitioner",
        "identifier": [{"system": "http://hospital.org/providers", "value": "567"}],
        "name": [{"family": "Smith", "given": ["John"]}],
    }


def valid_encounter():
    return {
        "resourceType": "Encounter",
        "id": "enc001",
        "status": "in-progress",
        "subject": {"reference": "Patient/12345"},
        "appointment": [{"reference": "Appointment/appt001"}],
        "participant": [{"individual": {"reference": "Practitioner/567"}}],
        "location": [{"location": {"reference": "Location/clinic-room-5"}}],
        "serviceProvider": {"reference": "Organization/sjafb"},
    }


def test_patient_checkin_success():
    result = process_patient_checkin(
        valid_patient(),
        valid_appointment(),
        valid_organization(),
        valid_location(),
        valid_practitioner(),
        valid_encounter(),
    )

    assert result["valid"] is True
    assert result["patient_checked_in"] is True
    assert result["errors"] == []


def test_patient_checkin_fails_when_appointment_cancelled():
    appointment = valid_appointment()
    appointment["status"] = "cancelled"

    result = process_patient_checkin(
        valid_patient(),
        appointment,
        valid_organization(),
        valid_location(),
        valid_practitioner(),
        valid_encounter(),
    )

    assert result["valid"] is False
    assert "Appointment is not in a check-in eligible status" in result["errors"]


def test_patient_checkin_fails_when_encounter_cancelled():
    encounter = valid_encounter()
    encounter["status"] = "cancelled"

    result = process_patient_checkin(
        valid_patient(),
        valid_appointment(),
        valid_organization(),
        valid_location(),
        valid_practitioner(),
        encounter,
    )

    assert result["valid"] is False
    assert "Encounter is not in an active clinical status" in result["errors"]