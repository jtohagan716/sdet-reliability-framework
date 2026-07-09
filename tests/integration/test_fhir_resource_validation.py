import json
from pathlib import Path


FHIR_DATA_DIR = Path("test_data/fhir")
INVALID_FHIR_DATA_DIR = FHIR_DATA_DIR / "invalid"


def load_fhir_resource(filename: str) -> dict:
    """
    Load a synthetic FHIR resource from the local test_data/fhir folder.
    """
    resource_path = FHIR_DATA_DIR / filename

    with resource_path.open("r", encoding="utf-8") as resource_file:
        return json.load(resource_file)


def load_invalid_fhir_resource(filename: str) -> dict:
    """
    Load an intentionally invalid synthetic FHIR resource.

    These fixtures are used for negative validation tests.
    """
    resource_path = INVALID_FHIR_DATA_DIR / filename

    with resource_path.open("r", encoding="utf-8") as resource_file:
        return json.load(resource_file)


def get_resource_reference(resource: dict) -> str:
    """
    Return the local FHIR-style reference for a resource.

    Example:
        Patient/example-patient-001
    """
    return f"{resource['resourceType']}/{resource['id']}"


def build_resource_reference_index(resources: list[dict]) -> set[str]:
    """
    Build an index of resource references that exist in the supplied dataset.
    """
    return {
        get_resource_reference(resource)
        for resource in resources
    }


def collect_declared_references(resource: dict) -> list[str]:
    """
    Collect local references declared by a synthetic FHIR resource.

    This intentionally starts with the reference fields used by this project:
    subject, encounter, and DiagnosticReport.result.
    """
    references = []

    if "subject" in resource and "reference" in resource["subject"]:
        references.append(resource["subject"]["reference"])

    if "encounter" in resource and "reference" in resource["encounter"]:
        references.append(resource["encounter"]["reference"])

    if resource.get("resourceType") == "DiagnosticReport":
        for result in resource.get("result", []):
            if "reference" in result:
                references.append(result["reference"])

    return references


def find_unresolved_references(resources: list[dict]) -> list[dict]:
    """
    Find references that point to resources not present in the supplied dataset.
    """
    existing_references = build_resource_reference_index(resources)
    unresolved_references = []

    for resource in resources:
        source_reference = get_resource_reference(resource)

        for declared_reference in collect_declared_references(resource):
            if declared_reference not in existing_references:
                unresolved_references.append(
                    {
                        "source": source_reference,
                        "missing_reference": declared_reference,
                    }
                )

    return unresolved_references


def load_valid_resource_chain() -> list[dict]:
    """
    Load the valid synthetic FHIR-style resource chain.
    """
    return [
        load_fhir_resource("patient-example.json"),
        load_fhir_resource("encounter-example.json"),
        load_fhir_resource("observation-example.json"),
        load_fhir_resource("diagnosticreport-example.json"),
    ]


def test_synthetic_fhir_resources_have_expected_resource_types():
    """
    Validate that each synthetic FHIR fixture declares the expected resourceType.
    """
    patient, encounter, observation, diagnostic_report = load_valid_resource_chain()

    assert patient["resourceType"] == "Patient"
    assert encounter["resourceType"] == "Encounter"
    assert observation["resourceType"] == "Observation"
    assert diagnostic_report["resourceType"] == "DiagnosticReport"


def test_synthetic_fhir_resources_form_expected_reference_chain():
    """
    Validate the expected happy-path healthcare interoperability chain.
    """
    patient, encounter, observation, diagnostic_report = load_valid_resource_chain()

    patient_reference = get_resource_reference(patient)
    encounter_reference = get_resource_reference(encounter)
    observation_reference = get_resource_reference(observation)

    assert encounter["subject"]["reference"] == patient_reference

    assert observation["subject"]["reference"] == patient_reference
    assert observation["encounter"]["reference"] == encounter_reference

    assert diagnostic_report["subject"]["reference"] == patient_reference
    assert diagnostic_report["encounter"]["reference"] == encounter_reference

    diagnostic_report_result_references = [
        result["reference"]
        for result in diagnostic_report["result"]
    ]

    assert observation_reference in diagnostic_report_result_references


def test_valid_synthetic_fhir_resources_have_no_unresolved_references():
    """
    Validate that every declared local reference in the happy-path fixture set
    points to a resource that exists in the same synthetic dataset.
    """
    resources = load_valid_resource_chain()

    unresolved_references = find_unresolved_references(resources)

    assert unresolved_references == []


def test_broken_diagnostic_report_reference_is_detected():
    """
    Validate that the test framework catches a broken DiagnosticReport.result
    reference.

    The broken DiagnosticReport points to:

        Observation/example-observation-missing-001

    That Observation is intentionally not present in the fixture set.
    """
    patient = load_fhir_resource("patient-example.json")
    encounter = load_fhir_resource("encounter-example.json")
    observation = load_fhir_resource("observation-example.json")
    broken_diagnostic_report = load_invalid_fhir_resource(
        "diagnosticreport-broken-observation-reference.json"
    )

    resources = [
        patient,
        encounter,
        observation,
        broken_diagnostic_report,
    ]

    unresolved_references = find_unresolved_references(resources)

    assert {
        "source": "DiagnosticReport/example-diagnosticreport-broken-001",
        "missing_reference": "Observation/example-observation-missing-001",
    } in unresolved_references