from framework.api.synthetic_journeys import (
    retrieve_patient_demographics,
    retrieve_patient_demographics_with_missing_last_name,
)


def test_patient_demographics_journey():

    result = retrieve_patient_demographics()

    assert result["success"] is True

    assert result["journey"] == (
        "Retrieve Patient Demographics"
    )

    assert result["contract"]["valid"] is True


def test_patient_demographics_journey_fails_when_contract_invalid():

    result = retrieve_patient_demographics_with_missing_last_name()

    assert result["success"] is False

    assert result["contract"]["valid"] is False

    assert result["contract"]["missing_fields"] == ["lastName"]

    assert result["failure_reason"] == (
        "Missing required demographics field"
    )