class ReliabilityAlertEngine:

    def evaluate_dashboard(self, dashboard_summary):

        degraded = dashboard_summary["health_counts"].get(
            "DEGRADED", 0
        )

        if degraded > 0:
            return {
                "alert": True,
                "severity": "HIGH",
                "message": "One or more synthetic transactions are degraded.",
            }

        return {
            "alert": False,
            "severity": "NONE",
            "message": "No operational alerts.",
        }