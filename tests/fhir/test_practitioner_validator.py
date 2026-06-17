from framework.fhir.practitioner_validator import validate_practitioner_resource


def test_valid_practitioner():

    practitioner = {
        "resourceType": "Practitioner",
        "identifier": [
            {
                "system": "http://hospital.org/providers",
                "value": "567",
            }
        ],
        "name": [
            {
                "family": "Smith",
                "given": ["John"],
            }
        ],
    }

    result = validate_practitioner_resource(practitioner)

    assert result["valid"] is True
    assert result["errors"] == []


def test_practitioner_requires_identifier():

    practitioner = {
        "resourceType": "Practitioner",
        "name": [
            {
                "family": "Smith",
                "given": ["John"],
            }
        ],
    }

    result = validate_practitioner_resource(practitioner)

    assert result["valid"] is False
    assert "identifier is required" in result["errors"]


def test_practitioner_requires_name():

    practitioner = {
        "resourceType": "Practitioner",
        "identifier": [
            {
                "system": "http://hospital.org/providers",
                "value": "567",
            }
        ],
    }

    result = validate_practitioner_resource(practitioner)

    assert result["valid"] is False
    assert "name is required" in result["errors"]


def test_practitioner_rejects_wrong_resource_type():

    practitioner = {
        "resourceType": "Patient",
        "identifier": [
            {
                "system": "http://hospital.org/providers",
                "value": "567",
            }
        ],
        "name": [
            {
                "family": "Smith",
                "given": ["John"],
            }
        ],
    }

    result = validate_practitioner_resource(practitioner)

    assert result["valid"] is False
    assert "resourceType must be Practitioner" in result["errors"]