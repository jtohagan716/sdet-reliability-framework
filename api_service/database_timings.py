from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class DatabasePhaseTimings:
    connect_ms: float = 0.0
    query_ms: float = 0.0
    fetch_ms: float = 0.0
    close_ms: float = 0.0
    total_ms: float = 0.0

    def as_dict(self) -> dict[str, float]:
        return {
            key: round(value, 3)
            for key, value in asdict(self).items()
        }
