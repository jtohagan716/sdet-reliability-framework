from framework.baselines.baseline_manager import evaluate_latency


def test_api_health_latency_is_healthy_against_baseline():
    result = evaluate_latency(
        current_ms=84,
        baseline_ms=100,
    )

    assert result["status"] == "HEALTHY"
    assert result["ratio"] == 0.84


def test_api_health_latency_enters_watch_when_slower():
    result = evaluate_latency(
        current_ms=200,
        baseline_ms=100,
    )

    assert result["status"] == "WATCH"


def test_api_health_latency_degrades_when_far_slower():
    result = evaluate_latency(
        current_ms=400,
        baseline_ms=100,
    )

    assert result["status"] == "DEGRADED"