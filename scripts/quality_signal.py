from dataclasses import dataclass


@dataclass
class QualitySignal:
    name: str
    status: str
    category: str
    total: int | None = None
    passed: int | None = None
    failed: int | None = None