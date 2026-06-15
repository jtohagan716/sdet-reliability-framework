from framework.api.synthetic_journeys import (
    retrieve_patient_demographics
)


def test_patient_demographics_journey():

    result = retrieve_patient_demographics()

    assert result["success"] is True

    assert result["journey"] == (
        "Retrieve Patient Demographics"
    )

    assert (
        result["contract"]["valid"]
        is True
    )