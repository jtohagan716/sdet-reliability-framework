from dataclasses import dataclass, field

from scripts.quality_signal import QualitySignal


@dataclass
class ReleaseAssessment:
    signals: list[QualitySignal] = field(default_factory=list)

    @property
    def total_checks(self) -> int:
        return len(self.signals)

    @property
    def failed_signals(self) -> list[QualitySignal]:
        return [
            signal for signal in self.signals
            if signal.status != "PASS"
        ]

    @property
    def failed_checks(self) -> int:
        return len(self.failed_signals)

    @property
    def overall_status(self) -> str:
        return (
            "READY FOR RELEASE"
            if self.failed_checks == 0
            else "BLOCK RELEASE"
        )

    @property
    def risk_level(self) -> str:
        if self.failed_checks == 0:
            return "LOW"

        if self.failed_checks == 1:
            return "MEDIUM"

        if self.failed_checks <= 3:
            return "HIGH"

        return "CRITICAL"

    @property
    def recommendation(self) -> str:
        if self.failed_checks == 0:
            return "Proceed with release."

        failed_names = ", ".join(signal.name for signal in self.failed_signals)
        return f"Block release until failing checks are resolved: {failed_names}."