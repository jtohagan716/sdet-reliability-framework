REQUIRED_DEMOGRAPHICS_FIELDS = [
    "patientId",
    "firstName",
    "lastName",
    "dob",
]


def validate_required_fields(data: dict, required_fields: list[str]) -> dict:
    missing_fields = []

    for field in required_fields:
        if field not in data:
            missing_fields.append(field)

    return {
        "valid": len(missing_fields) == 0,
        "missing_fields": missing_fields,
    }


def validate_demographics_contract(data: dict) -> dict:
    return validate_required_fields(
        data=data,
        required_fields=REQUIRED_DEMOGRAPHICS_FIELDS,
    )