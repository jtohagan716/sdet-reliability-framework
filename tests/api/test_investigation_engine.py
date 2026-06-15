from framework.api.investigation_engine import investigate_failure


def test_investigate_demographics_failure():

    result = investigate_failure(
        "PROVIDER_OPEN_PATIENT_CHART_DEMOGRAPHICS_FAILURE"
    )

    assert result["priority"] == "HIGH"

    assert (
        "Verify demographics contract validation results."
        in result["checks"]
    )


def test_investigate_unknown_failure():

    result = investigate_failure(
        "UNKNOWN_FAILURE_SIGNATURE"
    )

    assert result["priority"] == "UNKNOWN"

    assert (
        "No investigation guidance available for this failure signature."
        in result["checks"]
    )