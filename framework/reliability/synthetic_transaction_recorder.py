from datetime import datetime, UTC

from framework.reliability.canary_history import CanaryHistory
from framework.reliability.canary_trend_analyzer import analyze_canary_trend
from framework.reliability.canary_health import classify_canary_health
from framework.reliability.operational_decision import make_operational_decision


class SyntheticTransactionRecorder:

    def __init__(self, data_store):
        self.data_store = data_store
        self.histories = {}

    def record_result(self, canary_result):
        journey_name = canary_result.journey_name

        if journey_name not in self.histories:
            self.histories[journey_name] = CanaryHistory()

        history = self.histories[journey_name]
        history.add_result(canary_result.duration_ms)

        trend = analyze_canary_trend(history)
        health = classify_canary_health(trend)
        decision = make_operational_decision(health)

        self.data_store.initialize()

        self.data_store.save_synthetic_result(
            timestamp=datetime.now(UTC).isoformat(),
            journey_name=journey_name,
            status=canary_result.status,
            duration_ms=canary_result.duration_ms,
            signal=canary_result.signal,
            health=health["health"],
            decision=decision["decision"],
        )

        return {
            "journey_name": journey_name,
            "trend": trend["trend"],
            "health": health["health"],
            "decision": decision["decision"],
        }