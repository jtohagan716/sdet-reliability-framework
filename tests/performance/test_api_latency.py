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

    write_csv_report(result)
    write_json_report(result)

    assert "avg_ms" in result
    assert "stdev_ms" in result

    assert result["status"] == "PASS"