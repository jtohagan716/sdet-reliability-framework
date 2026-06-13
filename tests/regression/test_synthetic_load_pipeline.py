from framework.reliability.reliability_data_store import ReliabilityDataStore
from framework.reliability.synthetic_load_generator import SyntheticLoadGenerator
from framework.reliability.synthetic_load_pipeline import SyntheticLoadPipeline


def test_synthetic_load_pipeline_stores_statistics(tmp_path):
    db = tmp_path / "pipeline.db"

    store = ReliabilityDataStore(db_path=db)

    generator = SyntheticLoadGenerator(
        "http://127.0.0.1:8000"
    )

    pipeline = SyntheticLoadPipeline(
        load_generator=generator,
        data_store=store,
    )

    result = pipeline.run_and_store(
        journey_name="echo_normal",
        mode="normal",
        iterations=3,
    )

    stored = store.fetch_results_by_journey("echo_normal")

    assert result["journey_name"] == "echo_normal"
    assert result["mode"] == "normal"
    assert result["statistics"]["count"] == 3

    assert len(stored) == 1
    assert stored[0]["journey_name"] == "echo_normal"
    assert 100 <= stored[0]["duration_ms"] <= 500