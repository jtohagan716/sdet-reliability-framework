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