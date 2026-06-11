from framework.performance.runner import run_performance_suite


def test_api_latency_pipeline():
    result = run_performance_suite(
        url="https://example.com",
        iterations=8,
        threshold_ms=3000,
    )

    assert "avg_ms" in result
    assert "p95_ms" in result
    assert "p99_ms" in result
    assert "stdev_ms" in result

    assert "baseline" in result
    assert "regression" in result
    assert "p95_regression" in result
    assert "trend" in result

    assert "reliability_score" in result
    assert "verdict" in result
    assert "score_breakdown" in result

    assert "risk_level" in result
    assert "risk_points" in result

    assert "release_decision" in result
    assert "release_reason" in result

    assert result["status"] in [
        "PASS",
        "FAIL_BASELINE",
        "FAIL_TREND",
        "FAIL_STABILITY",
    ]

    assert result["release_decision"] in [
        "APPROVED",
        "APPROVED_WITH_RISK",
        "REQUIRES_REVIEW",
        "BLOCK_RELEASE",
    ]

    assert isinstance(result["reliability_score"], (int, float))
    assert 0 <= result["reliability_score"] <= 100

    assert isinstance(result["score_breakdown"], dict)