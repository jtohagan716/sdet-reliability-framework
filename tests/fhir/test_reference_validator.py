from framework.fhir.reference_validator import validate_reference


def test_valid_reference():

    errors = validate_reference(
        "Patient/12345",
        "Patient/12345",
        "Patient",
    )

    assert errors == []


def test_invalid_patient_reference():

    errors = validate_reference(
        "Patient/99999",
        "Patient/12345",
        "Patient",
    )

    assert errors == ["Patient reference is invalid"]


def test_invalid_appointment_reference():

    errors = validate_reference(
        "Appointment/appt999",
        "Appointment/appt001",
        "Appointment",
    )

    assert errors == ["Appointment reference is invalid"]