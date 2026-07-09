import json
from pathlib import Path


FHIR_DATA_DIR = Path("test_data/fhir")


def load_fhir_resource(filename: str) -> dict:
    """
    Load a synthetic FHIR resource from the local test_data/fhir folder.
    """
    resource_path = FHIR_DATA_DIR / filename

    with resource_path.open("r", encoding="utf-8") as resource_file:
        return json.load(resource_file)


def test_synthetic_fhir_resources_have_expected_resource_types():
    """
    Validate that each synthetic FHIR fixture declares the expected resourceType.

    This is the first layer of FHIR-style validation:
    the file should identify what kind of healthcare resource it represents.
    """

    patient = load_fhir_resource("patient-example.json")
    encounter = load_fhir_resource("encounter-example.json")
    observation = load_fhir_resource("observation-example.json")
    diagnostic_report = load_fhir_resource("diagnosticreport-example.json")

    assert patient["resourceType"] == "Patient"
    assert encounter["resourceType"] == "Encounter"
    assert observation["resourceType"] == "Observation"
    assert diagnostic_report["resourceType"] == "DiagnosticReport"


def test_synthetic_fhir_resources_form_expected_reference_chain():
    """
    Validate cross-resource reference integrity.

    Expected synthetic chain:

    Patient/example-patient-001
      -> Encounter/example-encounter-001
        -> Observation/example-observation-001
          -> DiagnosticReport/example-diagnosticreport-001

    This proves the test data forms a consistent healthcare interoperability
    chain before introducing a local FHIR server or SQL projection layer.
    """

    patient = load_fhir_resource("patient-example.json")
    encounter = load_fhir_resource("encounter-example.json")
    observation = load_fhir_resource("observation-example.json")
    diagnostic_report = load_fhir_resource("diagnosticreport-example.json")

    patient_reference = f"Patient/{patient['id']}"
    encounter_reference = f"Encounter/{encounter['id']}"
    observation_reference = f"Observation/{observation['id']}"

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