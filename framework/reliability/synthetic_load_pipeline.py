from datetime import datetime, UTC

from framework.reliability.transaction_statistics import TransactionStatistics


class SyntheticLoadPipeline:

    def __init__(self, load_generator, data_store):
        self.load_generator = load_generator
        self.data_store = data_store
        self.statistics = TransactionStatistics()

    def run_and_store(self, journey_name, mode="normal", iterations=5):
        latencies = self.load_generator.run(
            mode=mode,
            iterations=iterations,
        )

        stats = self.statistics.calculate(latencies)

        self.data_store.initialize()

        self.data_store.save_synthetic_result(
            timestamp=datetime.now(UTC).isoformat(),
            journey_name=journey_name,
            status="PASS",
            duration_ms=stats["average"],
            signal="HEALTHY",
            health="HEALTHY",
            decision="CONTINUE_MONITORING",
        )

        return {
            "journey_name": journey_name,
            "mode": mode,
            "statistics": stats,
        }