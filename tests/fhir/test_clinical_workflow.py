from framework.fhir.clinical_workflow import validate_clinical_workflow


def valid_patient():
    return {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hospital.org",
                "value": "12345",
            }
        ],
        "name": [
            {
                "family": "Doe",
                "given": ["Jane"],
            }
        ],
        "gender": "female",
        "birthDate": "1980-01-01",
    }


def valid_encounter():
    return {
        "resourceType": "Encounter",
        "id": "enc001",
        "status": "finished",
        "subject": {
            "reference": "Patient/12345",
        },
        "participant": [
            {
                "individual": {
                    "reference": "Practitioner/567",
                }
            }
        ],
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


def test_valid_clinical_workflow():

    result = validate_clinical_workflow(
        valid_patient(),
        valid_encounter(),
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_clinical_workflow_fails_when_patient_invalid():

    patient = valid_patient()
    patient.pop("identifier")

    result = validate_clinical_workflow(
        patient,
        valid_encounter(),
    )

    assert result["valid"] is False
    assert "identifier is required" in result["errors"]


def test_clinical_workflow_fails_when_encounter_invalid():

    encounter = valid_encounter()
    encounter.pop("participant")

    result = validate_clinical_workflow(
        valid_patient(),
        encounter,
    )

    assert result["valid"] is False
    assert "participant is required" in result["errors"]


def test_clinical_workflow_fails_when_encounter_references_wrong_patient():

    encounter = valid_encounter()
    encounter["subject"]["reference"] = "Patient/99999"

    result = validate_clinical_workflow(
        valid_patient(),
        encounter,
    )

    assert result["valid"] is False
    assert "Encounter references incorrect Patient" in result["errors"]