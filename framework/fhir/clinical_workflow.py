from framework.fhir.patient_validator import validate_patient_resource
from framework.fhir.appointment_validator import validate_appointment_resource
from framework.fhir.encounter_validator import validate_encounter_resource


def validate_clinical_workflow(
    patient: dict,
    appointment: dict,
    encounter: dict,
) -> dict:
    errors = []

    patient_result = validate_patient_resource(patient)
    if not patient_result["valid"]:
        errors.extend(patient_result["errors"])

    appointment_result = validate_appointment_resource(appointment)
    if not appointment_result["valid"]:
        errors.extend(appointment_result["errors"])

    encounter_result = validate_encounter_resource(encounter)
    if not encounter_result["valid"]:
        errors.extend(encounter_result["errors"])

    patient_id = _get_patient_identifier(patient)
    appointment_patient_reference = _get_appointment_patient_reference(appointment)
    encounter_patient_reference = _get_encounter_patient_reference(encounter)
    encounter_appointment_reference = _get_encounter_appointment_reference(encounter)

    if patient_id:
        expected_patient_reference = f"Patient/{patient_id}"

        if appointment_patient_reference and appointment_patient_reference != expected_patient_reference:
            errors.append("Appointment references incorrect Patient")

        if encounter_patient_reference and encounter_patient_reference != expected_patient_reference:
            errors.append("Encounter references incorrect Patient")

    appointment_id = appointment.get("id")

    if appointment_id:
        expected_appointment_reference = f"Appointment/{appointment_id}"

        if encounter_appointment_reference and encounter_appointment_reference != expected_appointment_reference:
            errors.append("Encounter references incorrect Appointment")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def _get_patient_identifier(patient: dict) -> str | None:
    identifiers = patient.get("identifier", [])

    if not identifiers:
        return None

    return identifiers[0].get("value")


def _get_appointment_patient_reference(appointment: dict) -> str | None:
    participants = appointment.get("participant", [])

    for participant in participants:
        actor = participant.get("actor", {})
        reference = actor.get("reference")

        if reference and reference.startswith("Patient/"):
            return reference

    return None


def _get_encounter_patient_reference(encounter: dict) -> str | None:
    subject = encounter.get("subject", {})

    return subject.get("reference")


def _get_encounter_appointment_reference(encounter: dict) -> str | None:
    appointment_refs = encounter.get("appointment", [])

    if not appointment_refs:
        return None

    return appointment_refs[0].get("reference")