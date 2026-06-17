from framework.fhir.validation_engine import (
    validate_required_fields,
    validate_resource_type,
)


def validate_practitioner_resource(practitioner: dict) -> dict:
    errors = []

    errors.extend(
        validate_resource_type(
            practitioner,
            "Practitioner",
        )
    )

    errors.extend(
        validate_required_fields(
            practitioner,
            [
                "identifier",
                "name",
            ],
        )
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }