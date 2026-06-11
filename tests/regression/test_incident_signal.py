from datetime import datetime

from framework.reliability.incident_signal import (
    IncidentSignal,
)


def test_incident_signal_creation():

    signal = IncidentSignal(
        timestamp=datetime(2026,6,11,9,15),

        source="TUXEDO_EMH",

        category="APPLICATION_ERROR",

        severity="ERROR",

        description="Error recorded by EMH.",
    )

    assert signal.source == "TUXEDO_EMH"

    assert signal.category == "APPLICATION_ERROR"

    assert signal.severity == "ERROR"