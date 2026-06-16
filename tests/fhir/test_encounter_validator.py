from framework.fhir.encounter_validator import (
    validate_encounter_resource,
)


def test_valid_encounter():

    encounter = {

        "resourceType": "Encounter",

        "id": "enc001",

        "status": "finished",

        "subject": {
            "reference": "Patient/12345"
        },

        "participant": [
            {
                "individual": {
                    "reference": "Practitioner/567",
                    "display": "Dr. Smith",
                }
            }
        ],

        "location": [
            {
                "location": {
                    "reference": "Location/clinic-room-5",
                    "display": "Exam Room 5",
                }
            }
        ],

        "serviceProvider": {
            "reference": "Organization/abc-clinic",
            "display": "ABC Health Clinic",
        },
    }

    result = validate_encounter_resource(
        encounter
    )

    assert result["valid"] is True
    result = validate_encounter_resource(
        encounter
    )

    assert result["valid"] is True


def test_missing_subject_reference():

    encounter = {

        "resourceType": "Encounter",

        "id": "enc001",

        "status": "finished",

        "subject": {},
    }

    result = validate_encounter_resource(
        encounter
    )

    assert result["valid"] is False

    assert (
        "subject reference is required"
        in result["errors"]
    )


def test_invalid_status():

    encounter = {

        "resourceType": "Encounter",

        "id": "enc001",

        "status": "banana",

        "subject": {
            "reference": "Patient/12345"
        },
    }

    result = validate_encounter_resource(
        encounter
    )

    assert result["valid"] is False

    assert (
        "status has invalid value"
        in result["errors"]
    )

def test_encounter_requires_provider_participant():

    encounter = {

        "resourceType": "Encounter",

        "id": "enc001",

        "status": "finished",

        "subject": {
            "reference": "Patient/12345"
        },

        "location": [
            {
                "location": {
                    "reference": "Location/clinic-room-5",
                }
            }
        ],

        "serviceProvider": {
            "reference": "Organization/abc-clinic",
        },
    }

    result = validate_encounter_resource(
        encounter
    )

    assert result["valid"] is False

    assert (
        "participant is required"
        in result["errors"]
    )