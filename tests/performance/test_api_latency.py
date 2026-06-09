from framework.performance.runner import run_performance_suite


def test_api_latency_pipeline():
    result = run_performance_suite(
        "https://example.com",
        iterations=8,
        threshold_ms=3000,
    )

    assert "avg_ms" in result
    assert "stdev_ms" in result

    assert result["status"] == "PASS"