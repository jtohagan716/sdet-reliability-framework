from framework.reliability.reliability_data_store import ReliabilityDataStore


def test_reliability_data_store_saves_synthetic_result(tmp_path):
    db_path = tmp_path / "test_reliability_data.db"

    store = ReliabilityDataStore(db_path=db_path)
    store.initialize()

    store.save_synthetic_result(
        timestamp="2026-06-12T09:00:00",
        journey_name="open_appointment_module",
        status="PASS",
        duration_ms=425,
        signal="HEALTHY",
        health="HEALTHY",
        decision="CONTINUE_MONITORING",
    )

    results = store.fetch_all_synthetic_results()

    assert len(results) == 1
    assert results[0]["journey_name"] == "open_appointment_module"
    assert results[0]["duration_ms"] == 425
    assert results[0]["decision"] == "CONTINUE_MONITORING"


def test_reliability_data_store_fetches_results_by_journey(tmp_path):
    db_path = tmp_path / "test_reliability_data.db"

    store = ReliabilityDataStore(db_path=db_path)
    store.initialize()

    store.save_synthetic_result(
        timestamp="2026-06-12T09:00:00",
        journey_name="open_appointment_module",
        status="PASS",
        duration_ms=425,
        signal="HEALTHY",
        health="HEALTHY",
        decision="CONTINUE_MONITORING",
    )

    store.save_synthetic_result(
        timestamp="2026-06-12T09:05:00",
        journey_name="create_and_sign_encounter",
        status="PASS",
        duration_ms=700,
        signal="HEALTHY",
        health="WATCH",
        decision="MONITOR_CLOSELY",
    )

    results = store.fetch_results_by_journey("open_appointment_module")

    assert len(results) == 1
    assert results[0]["journey_name"] == "open_appointment_module"
    assert results[0]["duration_ms"] == 425