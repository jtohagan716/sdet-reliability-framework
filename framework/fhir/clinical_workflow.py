from framework.fhir.patient_validator import validate_patient_resource
from framework.fhir.encounter_validator import validate_encounter_resource


def validate_clinical_workflow(patient: dict, encounter: dict) -> dict:
    errors = []

    patient_result = validate_patient_resource(patient)
    if not patient_result["valid"]:
        errors.extend(patient_result["errors"])

    encounter_result = validate_encounter_resource(encounter)
    if not encounter_result["valid"]:
        errors.extend(encounter_result["errors"])

    if (
        patient.get("identifier")
        and encounter.get("subject")
        and encounter["subject"].get("reference")
    ):
        patient_id = patient["identifier"][0].get("value")
        expected_reference = f"Patient/{patient_id}"

        if encounter["subject"]["reference"] != expected_reference:
            errors.append("Encounter references incorrect Patient")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }