from dataclasses import dataclass
from datetime import datetime


@dataclass
class TimelineEvent:
    timestamp: datetime
    source: str
    signal_type: str
    severity: str
    message: str


class IncidentTimeline:

    def __init__(self):
        self.events = []

    def add_event(self, event: TimelineEvent):
        self.events.append(event)

    def ordered_events(self):
        return sorted(
            self.events,
            key=lambda event: event.timestamp,
        )

    def count(self):
        return len(self.events)

    def sources(self):
        return sorted(
            set(event.source for event in self.events)
        )