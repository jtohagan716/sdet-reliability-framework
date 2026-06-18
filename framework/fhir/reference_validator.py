def validate_reference(
    actual_reference: str,
    expected_reference: str,
    resource_name: str,
) -> list[str]:

    if actual_reference != expected_reference:
        return [f"{resource_name} reference is invalid"]

    return []