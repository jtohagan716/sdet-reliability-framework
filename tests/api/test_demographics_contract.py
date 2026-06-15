from framework.api.contracts import validate_demographics_contract


def test_demographics_contract_passes_when_required_fields_exist():
    response = {
        "patientId": "12345",
        "firstName": "John",
        "lastName": "Smith",
        "dob": "1970-01-01",
    }

    result = validate_demographics_contract(response)

    assert result["valid"] is True
    assert result["missing_fields"] == []


def test_demographics_contract_fails_when_required_field_missing():
    response = {
        "patientId": "12345",
        "firstName": "John",
        "dob": "1970-01-01",
    }

    result = validate_demographics_contract(response)

    assert result["valid"] is False
    assert result["missing_fields"] == ["lastName"]