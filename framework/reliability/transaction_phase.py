from dataclasses import dataclass


@dataclass
class TransactionPhase:
    name: str
    component: str
    elapsed_ms: float
    status: str = "SUCCESS"