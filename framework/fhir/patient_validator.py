from framework.fhir.validation_engine import (
    validate_allowed_values,
    validate_required_fields,
    validate_resource_type,
)


VALID_GENDERS = ["male", "female", "other", "unknown"]


def validate_patient_resource(patient: dict) -> dict:
    errors = []

    errors.extend(
        validate_resource_type(patient, "Patient")
    )

    errors.extend(
        validate_required_fields(
            patient,
            ["identifier", "name", "birthDate"],
        )
    )

    errors.extend(
        validate_allowed_values(
            patient,
            "gender",
            VALID_GENDERS,
        )
    )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }