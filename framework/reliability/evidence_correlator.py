def correlate_evidence(timeline):

    events = timeline.ordered_events()

    if not events:
        return {
            "source_count": 0,
            "sources": [],
            "confidence": "LOW",
            "incident_window": None,
        }

    sources = sorted(
        set(event.source for event in events)
    )

    source_count = len(sources)

    if source_count >= 4:
        confidence = "VERY_HIGH"
    elif source_count >= 3:
        confidence = "HIGH"
    elif source_count >= 2:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    window = (
        events[0].timestamp,
        events[-1].timestamp,
    )

    return {
        "source_count": source_count,
        "sources": sources,
        "confidence": confidence,
        "incident_window": window,
    }