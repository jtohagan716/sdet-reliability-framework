from framework.reliability.reliability_dashboard import ReliabilityDashboard
from framework.reliability.reliability_data_store import ReliabilityDataStore
from framework.reliability.reliability_alert_engine import ReliabilityAlertEngine
from framework.reliability.operational_shift_handoff import OperationalShiftHandoff


def test_operational_shift_handoff(tmp_path):
    db = tmp_path / "handoff.db"

    store = ReliabilityDataStore(db_path=db)
    store.initialize()

    store.save_synthetic_result(
        "2026-06-13T00:00:00+00:00",
        "provider_login",
        "PASS",
        300,
        "HEALTHY",
        "HEALTHY",
        "CONTINUE_MONITORING",
    )

    dashboard = ReliabilityDashboard(store)
    alerts = ReliabilityAlertEngine()
    handoff = OperationalShiftHandoff(dashboard, alerts)

    report = handoff.generate_handoff()

    assert report["platform_status"] == "GREEN"
    assert report["total_transactions"] == 1
    assert report["health_counts"]["HEALTHY"] == 1
    assert report["alert"]["alert"] is False