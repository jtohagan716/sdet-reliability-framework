from framework.fhir.validation_engine import (
    validate_allowed_values,
    validate_required_fields,
    validate_resource_type,
)


def test_validate_required_fields_passes_when_fields_exist():

    resource = {
        "resourceType": "Patient",
        "identifier": [{"value": "12345"}],
        "name": [{"family": "Smith"}],
    }

    errors = validate_required_fields(
        resource,
        ["resourceType", "identifier", "name"],
    )

    assert errors == []


def test_validate_required_fields_fails_when_field_missing():

    resource = {
        "resourceType": "Patient",
        "name": [{"family": "Smith"}],
    }

    errors = validate_required_fields(
        resource,
        ["resourceType", "identifier", "name"],
    )

    assert "identifier is required" in errors


def test_validate_allowed_values_rejects_invalid_value():

    resource = {
        "resourceType": "Patient",
        "gender": "not-a-real-gender",
    }

    errors = validate_allowed_values(
        resource,
        "gender",
        ["male", "female", "other", "unknown"],
    )

    assert "gender has invalid value" in errors


def test_validate_resource_type_rejects_wrong_type():

    resource = {
        "resourceType": "Encounter",
    }

    errors = validate_resource_type(resource, "Patient")

    assert "resourceType must be Patient" in errors