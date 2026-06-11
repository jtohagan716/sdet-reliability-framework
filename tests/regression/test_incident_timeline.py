from datetime import datetime

from framework.reliability.incident_timeline import (
    IncidentTimeline,
    TimelineEvent,
)


def test_incident_timeline_orders_events_by_timestamp():
    timeline = IncidentTimeline()

    timeline.add_event(
        TimelineEvent(
            timestamp=datetime(2026, 6, 11, 9, 10),
            source="CDRPLUS.ERROR_LOG",
            signal_type="APPLICATION_ERROR",
            severity="ERROR",
            message="Open Appointment error detected.",
        )
    )

    timeline.add_event(
        TimelineEvent(
            timestamp=datetime(2026, 6, 11, 9, 5),
            source="ARM_CLIENT",
            signal_type="CLIENT_TIMING",
            severity="WARN",
            message="Open Appointment latency exceeded baseline.",
        )
    )

    ordered = timeline.ordered_events()

    assert ordered[0].source == "ARM_CLIENT"
    assert ordered[1].source == "CDRPLUS.ERROR_LOG"


def test_incident_timeline_tracks_sources():
    timeline = IncidentTimeline()

    timeline.add_event(
        TimelineEvent(
            timestamp=datetime(2026, 6, 11, 9, 5),
            source="ARM_CLIENT",
            signal_type="CLIENT_TIMING",
            severity="WARN",
            message="Client latency warning.",
        )
    )

    timeline.add_event(
        TimelineEvent(
            timestamp=datetime(2026, 6, 11, 9, 7),
            source="TUXEDO_EMH",
            signal_type="MIDDLEWARE_ERROR",
            severity="ERROR",
            message="Error recorded by Error Message Handler.",
        )
    )

    assert timeline.count() == 2
    assert timeline.sources() == [
        "ARM_CLIENT",
        "TUXEDO_EMH",
    ]