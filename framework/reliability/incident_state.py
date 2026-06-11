from dataclasses import dataclass


@dataclass
class IncidentState:
    state: str
    severity: str
    scope: str
    confidence: str
    primary_owner: str