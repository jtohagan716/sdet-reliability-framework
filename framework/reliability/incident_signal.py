from dataclasses import dataclass
from datetime import datetime


@dataclass
class IncidentSignal:
    timestamp: datetime

    source: str

    category: str

    severity: str

    description: str