from framework.fhir.patient_validator import validate_patient_resource


def test_valid_patient_resource():

    patient = {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hospital.org",
                "value": "AUTOTEST-12345",
            }
        ],
        "name": [
            {
                "family": "Smith",
                "given": ["John"],
            }
        ],
        "gender": "male",
        "birthDate": "1980-01-01",
    }

    result = validate_patient_resource(patient)

    assert result["valid"] is True
    assert result["errors"] == []


def test_patient_resource_requires_identifier():

    patient = {
        "resourceType": "Patient",
        "name": [
            {
                "family": "Smith",
                "given": ["John"],
            }
        ],
        "gender": "male",
        "birthDate": "1980-01-01",
    }

    result = validate_patient_resource(patient)

    assert result["valid"] is False
    assert "Patient identifier is required" in result["errors"]


def test_patient_resource_rejects_invalid_gender():

    patient = {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hospital.org",
                "value": "AUTOTEST-12345",
            }
        ],
        "name": [
            {
                "family": "Smith",
                "given": ["John"],
            }
        ],
        "gender": "invalid-value",
        "birthDate": "1980-01-01",
    }

    result = validate_patient_resource(patient)

    assert result["valid"] is False
    assert "Patient gender is invalid" in result["errors"]