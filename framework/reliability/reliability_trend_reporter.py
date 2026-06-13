class ReliabilityTrendReporter:

    def generate(self, results):

        if not results:
            return {
                "count": 0,
                "average_latency": 0,
                "trend": "UNKNOWN",
            }

        count = len(results)

        average = sum(
            r["duration_ms"]
            for r in results
        ) / count

        latest = results[-1]["duration_ms"]

        if latest <= average:
            trend = "STABLE"

        else:
            trend = "DEGRADING"

        return {
            "count": count,
            "average_latency": average,
            "latest_latency": latest,
            "trend": trend,
        }