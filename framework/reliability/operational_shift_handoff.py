from datetime import datetime, UTC


class OperationalShiftHandoff:

    def __init__(self, dashboard, alert_engine):
        self.dashboard = dashboard
        self.alert_engine = alert_engine

    def generate_handoff(self):
        summary = self.dashboard.generate_summary()
        alert = self.alert_engine.evaluate_dashboard(summary)

        return {
            "timestamp": datetime.now(UTC).isoformat(),
            "platform_status": "GREEN" if not alert["alert"] else "ATTENTION",
            "total_transactions": summary["total_transactions"],
            "health_counts": summary["health_counts"],
            "decision_counts": summary["decision_counts"],
            "alert": alert,
        }