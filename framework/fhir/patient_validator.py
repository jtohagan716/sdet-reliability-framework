VALID_GENDERS = ["male", "female", "other", "unknown"]


def validate_patient_resource(patient: dict) -> dict:
    errors = []

    if patient.get("resourceType") != "Patient":
        errors.append("resourceType must be Patient")

    if "identifier" not in patient or not patient["identifier"]:
        errors.append("Patient identifier is required")

    if "name" not in patient or not patient["name"]:
        errors.append("Patient name is required")

    if "birthDate" not in patient:
        errors.append("Patient birthDate is required")

    if "gender" in patient and patient["gender"] not in VALID_GENDERS:
        errors.append("Patient gender is invalid")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
    }