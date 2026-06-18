from framework.fhir.organization_validator import (
    validate_organization_resource,
)


def test_valid_organization():

    organization = {
        "resourceType": "Organization",
        "id": "sjafb",
        "identifier": [
            {
                "system": "urn:ahlta:facility-ncid",
                "value": "1048021",
            }
        ],
        "name": "Seymour Johnson MTF",
    }

    result = validate_organization_resource(
        organization
    )

    assert result["valid"] is True
    assert result["errors"] == []


def test_organization_requires_identifier():

    organization = {
        "resourceType": "Organization",
        "id": "sjafb",
        "name": "Seymour Johnson MTF",
    }

    result = validate_organization_resource(
        organization
    )

    assert result["valid"] is False
    assert "identifier is required" in result["errors"]


def test_organization_requires_name():

    organization = {
        "resourceType": "Organization",
        "id": "sjafb",
        "identifier": [
            {
                "system": "urn:ahlta:facility-ncid",
                "value": "1048021",
            }
        ],
    }

    result = validate_organization_resource(
        organization
    )

    assert result["valid"] is False
    assert "name is required" in result["errors"]


def test_organization_rejects_wrong_resource_type():

    organization = {
        "resourceType": "Patient",
        "id": "sjafb",
        "identifier": [
            {
                "system": "urn:ahlta:facility-ncid",
                "value": "1048021",
            }
        ],
        "name": "Seymour Johnson MTF",
    }

    result = validate_organization_resource(
        organization
    )

    assert result["valid"] is False
    assert "resourceType must be Organization" in result["errors"]