from framework.fhir.validation_engine import (
    validate_required_fields,
    validate_allowed_values,
    validate_resource_type,
)


VALID_APPOINTMENT_STATUSES = [
    "proposed",
    "pending",
    "booked",
    "arrived",
    "fulfilled",
    "cancelled",
    "noshow",
    "entered-in-error",
    "checked-in",
    "waitlist",
]


def validate_appointment_resource(appointment: dict) -> dict:
    errors = []

    errors.extend(validate_resource_type(appointment, "Appointment"))

    errors.extend(
        validate_required_fields(
            appointment,
            ["id", "status", "participant"],
        )
    )

    errors.extend(
        validate_allowed_values(
            appointment,
            "status",
            VALID_APPOINTMENT_STATUSES,
        )
    )

    if "participant" in appointment:
        has_patient_reference = False

        for participant in appointment["participant"]:
            actor = participant.get("actor", {})
            reference = actor.get("reference", "")

            if reference.startswith("Patient/"):
                has_patient_reference = True

        if not has_patient_reference:
            errors.append("Appointment patient participant is required")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }