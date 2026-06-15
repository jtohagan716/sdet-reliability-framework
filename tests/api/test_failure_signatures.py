from framework.api.failure_signatures import (
    create_failure_signature
)


def test_failure_signature():

    signature = create_failure_signature(

        "Provider Open Patient Chart",

        "demographics"

    )

    assert signature == (

        "PROVIDER_OPEN_PATIENT_CHART_"

        "DEMOGRAPHICS_FAILURE"

    )