def validate_required_fields(resource: dict, required_fields: list[str]) -> list[str]:
    errors = []

    for field in required_fields:
        if field not in resource or resource[field] in [None, "", []]:
            errors.append(f"{field} is required")

    return errors


def validate_allowed_values(resource: dict, field: str, allowed_values: list[str]) -> list[str]:
    errors = []

    if field in resource and resource[field] not in allowed_values:
        errors.append(f"{field} has invalid value")

    return errors


def validate_resource_type(resource: dict, expected_type: str) -> list[str]:
    errors = []

    if resource.get("resourceType") != expected_type:
        errors.append(f"resourceType must be {expected_type}")

    return errors