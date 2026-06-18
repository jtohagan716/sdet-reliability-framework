from framework.fhir.validation_engine import (
    validate_required_fields,
    validate_resource_type,
)


def validate_organization_resource(
    organization: dict,
) -> dict:

    errors = []

    errors.extend(
        validate_resource_type(
            organization,
            "Organization",
        )
    )

    errors.extend(
        validate_required_fields(
            organization,
            [
                "id",
                "identifier",
                "name",
            ],
        )
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }