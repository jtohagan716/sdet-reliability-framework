from framework.fhir.patient_validator import validate_patient_resource
from framework.fhir.appointment_validator import validate_appointment_resource
from framework.fhir.organization_validator import validate_organization_resource
from framework.fhir.location_validator import validate_location_resource
from framework.fhir.practitioner_validator import validate_practitioner_resource
from framework.fhir.encounter_validator import validate_encounter_resource


def process_patient_checkin(
    patient: dict,
    appointment: dict,
    organization: dict,
    location: dict,
    practitioner: dict,
    encounter: dict,
) -> dict:
    errors = []

    validation_results = [
        validate_patient_resource(patient),
        validate_appointment_resource(appointment),
        validate_organization_resource(organization),
        validate_location_resource(location),
        validate_practitioner_resource(practitioner),
        validate_encounter_resource(encounter),
    ]

    for result in validation_results:
        if not result["valid"]:
            errors.extend(result["errors"])

    if appointment.get("status") not in ["booked", "arrived", "checked-in"]:
        errors.append("Appointment is not in a check-in eligible status")

    if encounter.get("status") not in ["arrived", "in-progress", "finished"]:
        errors.append("Encounter is not in an active clinical status")

    return {
        "valid": len(errors) == 0,
        "patient_checked_in": len(errors) == 0,
        "errors": errors,
    }