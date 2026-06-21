from framework.baselines.baseline_manager import evaluate_latency


def test_latency_at_baseline_is_healthy():
    result = evaluate_latency(100, 100)

    assert result["status"] == "HEALTHY"
    assert result["ratio"] == 1.0


def test_latency_slightly_above_baseline_is_healthy():
    result = evaluate_latency(140, 100)

    assert result["status"] == "HEALTHY"


def test_latency_moderately_above_baseline_is_watch():
    result = evaluate_latency(200, 100)

    assert result["status"] == "WATCH"


def test_latency_far_above_baseline_is_degraded():
    result = evaluate_latency(400, 100)

    assert result["status"] == "DEGRADED"