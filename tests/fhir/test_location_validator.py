from framework.fhir.location_validator import validate_location_resource


def test_valid_location():

    location = {
        "resourceType": "Location",
        "id": "clinic-room-5",
        "name": "Exam Room 5",
    }

    result = validate_location_resource(location)

    assert result["valid"] is True
    assert result["errors"] == []


def test_location_requires_id():

    location = {
        "resourceType": "Location",
        "name": "Exam Room 5",
    }

    result = validate_location_resource(location)

    assert result["valid"] is False
    assert "id is required" in result["errors"]


def test_location_requires_name():

    location = {
        "resourceType": "Location",
        "id": "clinic-room-5",
    }

    result = validate_location_resource(location)

    assert result["valid"] is False
    assert "name is required" in result["errors"]


def test_location_rejects_wrong_resource_type():

    location = {
        "resourceType": "Organization",
        "id": "clinic-room-5",
        "name": "Exam Room 5",
    }

    result = validate_location_resource(location)

    assert result["valid"] is False
    assert "resourceType must be Location" in result["errors"]