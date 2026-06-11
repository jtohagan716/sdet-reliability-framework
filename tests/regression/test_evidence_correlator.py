from datetime import datetime

from framework.reliability.incident_timeline import (
    IncidentTimeline,
    TimelineEvent,
)

from framework.reliability.evidence_correlator import (
    correlate_evidence,
)


def test_evidence_correlation():

    timeline = IncidentTimeline()

    timeline.add_event(
        TimelineEvent(
            datetime(2026,6,11,9,5),
            "ARM_CLIENT",
            "TIMING",
            "WARN",
            "Latency",
        )
    )

    timeline.add_event(
        TimelineEvent(
            datetime(2026,6,11,9,6),
            "TUXEDO_EMH",
            "ERROR",
            "ERROR",
            "Middleware",
        )
    )

    timeline.add_event(
        TimelineEvent(
            datetime(2026,6,11,9,7),
            "CDRPLUS.ERROR_LOG",
            "ERROR",
            "ERROR",
            "Application",
        )
    )

    result = correlate_evidence(
        timeline
    )

    assert result["source_count"] == 3
    assert result["confidence"] == "HIGH"


def test_empty_timeline():

    timeline = IncidentTimeline()

    result = correlate_evidence(
        timeline
    )

    assert result["source_count"] == 0
    assert result["confidence"] == "LOW"