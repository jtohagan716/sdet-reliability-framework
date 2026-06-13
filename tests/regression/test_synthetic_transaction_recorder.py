from framework.reliability.canary_result import CanaryResult
from framework.reliability.reliability_data_store import ReliabilityDataStore
from framework.reliability.synthetic_transaction_recorder import (
    SyntheticTransactionRecorder,
)


def test_synthetic_transaction_recorder_stores_result(tmp_path):
    db_path = tmp_path / "test_reliability_data.db"

    store = ReliabilityDataStore(db_path=db_path)
    recorder = SyntheticTransactionRecorder(data_store=store)

    canary_result = CanaryResult(
        journey_name="open_appointment_module",
        status="PASS",
        duration_ms=425,
        signal="HEALTHY",
        recommendation="No action required.",
    )

    result = recorder.record_result(canary_result)

    stored_results = store.fetch_results_by_journey("open_appointment_module")

    assert result["journey_name"] == "open_appointment_module"
    assert result["trend"] == "INSUFFICIENT_DATA"
    assert result["health"] == "UNKNOWN"
    assert result["decision"] == "COLLECT_MORE_EVIDENCE"

    assert len(stored_results) == 1
    assert stored_results[0]["journey_name"] == "open_appointment_module"
    assert stored_results[0]["duration_ms"] == 425


def test_synthetic_transaction_recorder_detects_degrading_trend(tmp_path):
    db_path = tmp_path / "test_reliability_data.db"

    store = ReliabilityDataStore(db_path=db_path)
    recorder = SyntheticTransactionRecorder(data_store=store)

    recorder.record_result(
        CanaryResult(
            journey_name="open_appointment_module",
            status="PASS",
            duration_ms=300,
            signal="HEALTHY",
            recommendation="No action required.",
        )
    )

    result = recorder.record_result(
        CanaryResult(
            journey_name="open_appointment_module",
            status="PASS",
            duration_ms=500,
            signal="HEALTHY",
            recommendation="Investigate latency.",
        )
    )

    stored_results = store.fetch_results_by_journey("open_appointment_module")

    assert result["trend"] == "DEGRADING"
    assert result["health"] == "DEGRADED"
    assert result["decision"] == "INVESTIGATE"

    assert len(stored_results) == 2