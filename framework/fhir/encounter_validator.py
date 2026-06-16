from framework.fhir.validation_engine import (
    validate_required_fields,
    validate_allowed_values,
    validate_resource_type,
)


VALID_STATUSES = [
    "planned",
    "arrived",
    "triaged",
    "in-progress",
    "onleave",
    "finished",
    "cancelled",
    "entered-in-error",
    "unknown",
]


def validate_encounter_resource(encounter: dict):

    errors = []

    errors.extend(
        validate_resource_type(
            encounter,
            "Encounter",
        )
    )

    errors.extend(
        validate_required_fields(
            encounter,
            [
                "id",
                "status",
                "subject",
            ],
        )
    )

    errors.extend(
        validate_allowed_values(
            encounter,
            "status",
            VALID_STATUSES,
        )
    )

    if "subject" in encounter:

        if "reference" not in encounter["subject"]:

            errors.append(
                "subject reference is required"
            )

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }