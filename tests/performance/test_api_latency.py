from framework.performance.runner import run_performance_suite

from framework.reporting.performance_reporter import (
    write_csv_report,
    write_json_report,
)


def test_api_latency_pipeline():
    result = run_performance_suite(
        "https://example.com",
        iterations=8,
        threshold_ms=3000,
    )

    # Persist performance intelligence artifacts
    write_csv_report(result)
    write_json_report(result)

    # Core telemetry contract
    assert "avg_ms" in result
    assert "stdev_ms" in result
    assert "p50_ms" in result
    assert "p95_ms" in result
    assert "p99_ms" in result

    # Reliability intelligence contract
    assert "regression" in result
    assert "p95_regression" in result
    assert "trend" in result
    assert "reliability_score" in result
    assert "verdict" in result

    # Release intelligence contract
    assert "risk_level" in result
    assert "risk_points" in result
    assert "release_decision" in result
    assert "release_reason" in result

    # Valid status outcomes
    assert result["status"] in [
        "PASS",
        "FAIL_BASELINE",
        "FAIL_TREND",
        "FAIL_STABILITY",
    ]