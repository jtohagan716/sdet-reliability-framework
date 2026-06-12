from dataclasses import dataclass


@dataclass
class CanaryResult:
    journey_name: str

    status: str

    duration_ms: float

    signal: str

    recommendation: str