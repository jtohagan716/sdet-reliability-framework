from framework.api.provider_workflows import (
    provider_open_patient_chart,
    provider_open_patient_chart_with_failed_search,
    provider_open_patient_chart_with_invalid_demographics,
)

def test_provider_workflow():

    result = provider_open_patient_chart()

    assert result["success"] is True

    assert result["workflow"] == (
        "Provider Open Patient Chart"
    )

def test_provider_workflow_fails_when_patient_search_fails():

    result = provider_open_patient_chart_with_failed_search()

    assert result["success"] is False

    assert result["workflow"] == (
        "Provider Open Patient Chart"
    )

    assert result["failed_step"] == "search"

    assert result["failure_reason"] == (
        "Patient search failed"
    )

def test_provider_workflow_fails_when_demographics_contract_invalid():

    result = provider_open_patient_chart_with_invalid_demographics()

    assert result["success"] is False

    assert result["workflow"] == (
        "Provider Open Patient Chart"
    )

    assert result["failed_step"] == "demographics"

    assert result["failure_reason"] == (
        "Demographics contract validation failed"
    )

    assert result["missing_fields"] == ["lastName"]    