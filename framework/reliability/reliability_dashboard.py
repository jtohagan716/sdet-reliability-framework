from collections import Counter


class ReliabilityDashboard:

    def __init__(self, data_store):
        self.data_store = data_store

    def generate_summary(self):
        records = self.data_store.fetch_all_synthetic_results()

        health = Counter()
        decisions = Counter()

        for record in records:
            health[record["health"]] += 1
            decisions[record["decision"]] += 1

        return {
            "total_transactions": len(records),
            "health_counts": dict(health),
            "decision_counts": dict(decisions),
        }