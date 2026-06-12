from framework.reliability.reliability_dashboard import ReliabilityDashboard
from framework.reliability.reliability_data_store import ReliabilityDataStore


def test_dashboard_summary(tmp_path):
    db = tmp_path / "dashboard.db"

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

    store.save_synthetic_result(
        "2026-06-13T01:00:00+00:00",
        "appointment_lookup",
        "PASS",
        700,
        "WATCH",
        "DEGRADED",
        "INVESTIGATE",
    )

    dashboard = ReliabilityDashboard(store)

    summary = dashboard.generate_summary()

    assert summary["total_transactions"] == 2
    assert summary["health_counts"]["HEALTHY"] == 1
    assert summary["health_counts"]["DEGRADED"] == 1
    assert summary["decision_counts"]["CONTINUE_MONITORING"] == 1
    assert summary["decision_counts"]["INVESTIGATE"] == 1