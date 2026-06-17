from framework.fhir.patient_validator import validate_patient_resource
from framework.fhir.appointment_validator import validate_appointment_resource
from framework.fhir.encounter_validator import validate_encounter_resource
from framework.fhir.practitioner_validator import validate_practitioner_resource


def validate_clinical_workflow(
    patient: dict,
    appointment: dict,
    encounter: dict,
    practitioner: dict,
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

    practitioner_result = validate_practitioner_resource(practitioner)
    if not practitioner_result["valid"]:
        errors.extend(practitioner_result["errors"])

    patient_id = _get_patient_identifier(patient)
    appointment_patient_reference = _get_appointment_patient_reference(appointment)
    encounter_patient_reference = _get_encounter_patient_reference(encounter)

    if patient_id:
        expected_patient_reference = f"Patient/{patient_id}"

        if (
            appointment_patient_reference
            and appointment_patient_reference != expected_patient_reference
        ):
            errors.append("Appointment references incorrect Patient")

        if (
            encounter_patient_reference
            and encounter_patient_reference != expected_patient_reference
        ):
            errors.append("Encounter references incorrect Patient")

    appointment_id = appointment.get("id")
    encounter_appointment_reference = _get_encounter_appointment_reference(encounter)

    if appointment_id:
        expected_appointment_reference = f"Appointment/{appointment_id}"

        if (
            encounter_appointment_reference
            and encounter_appointment_reference != expected_appointment_reference
        ):
            errors.append("Encounter references incorrect Appointment")

    practitioner_id = _get_practitioner_identifier(practitioner)
    encounter_practitioner_reference = _get_encounter_practitioner_reference(encounter)

    if practitioner_id:
        expected_practitioner_reference = f"Practitioner/{practitioner_id}"

        if (
            encounter_practitioner_reference
            and encounter_practitioner_reference != expected_practitioner_reference
        ):
            errors.append("Encounter references incorrect Practitioner")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }


def _get_patient_identifier(patient: dict) -> str | None:
    identifiers = patient.get("identifier", [])

    if not identifiers:
        return None

    return identifiers[0].get("value")


def _get_practitioner_identifier(practitioner: dict) -> str | None:
    identifiers = practitioner.get("identifier", [])

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


def _get_encounter_practitioner_reference(encounter: dict) -> str | None:
    participants = encounter.get("participant", [])

    if not participants:
        return None

    individual = participants[0].get("individual", {})

    return individual.get("reference")