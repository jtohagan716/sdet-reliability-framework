from framework.fhir.validation_engine import (
    validate_required_fields,
    validate_resource_type,
)


def validate_location_resource(location: dict) -> dict:
    errors = []

    errors.extend(
        validate_resource_type(
            location,
            "Location",
        )
    )

    errors.extend(
        validate_required_fields(
            location,
            [
                "id",
                "name",
            ],
        )
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }