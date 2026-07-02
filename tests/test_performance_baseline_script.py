from pathlib import Path

from scripts.run_performance_baseline import (
    RequestResult,
    percentile,
    summarize_results,
    write_markdown_report,
)


def test_percentile_returns_expected_value():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    assert percentile(values, 0.95) == 50.0


def test_summarize_results_counts_passes_and_failures():
    results = [
        RequestResult(
            scenario="health_check",
            path="/health",
            expected_status=200,
            actual_status=200,
            duration_ms=10.0,
            passed=True,
        ),
        RequestResult(
            scenario="patient_lookup_success",
            path="/patients/1001",
            expected_status=200,
            actual_status=200,
            duration_ms=20.0,
            passed=True,
        ),
        RequestResult(
            scenario="patient_lookup_not_found",
            path="/patients/9999",
            expected_status=404,
            actual_status=404,
            duration_ms=30.0,
            passed=True,
        ),
    ]

    summaries = summarize_results(results)

    assert len(summaries) == 3

    for summary in summaries:
        assert summary["count"] == 1
        assert summary["passed"] == 1
        assert summary["failed"] == 0
        assert summary["error_rate_percent"] == 0.0


def test_write_markdown_report_creates_expected_file(tmp_path):
    output_path = tmp_path / "performance_baseline.md"

    summaries = [
        {
            "scenario": "health_check",
            "path": "/health",
            "expected_status": 200,
            "count": 1,
            "passed": 1,
            "failed": 0,
            "error_rate_percent": 0.0,
            "avg_ms": 10.0,
            "min_ms": 10.0,
            "max_ms": 10.0,
            "p95_ms": 10.0,
        }
    ]

    write_markdown_report(
        output_path=Path(output_path),
        base_url="http://localhost:8000",
        iterations=1,
        summaries=summaries,
    )

    report_text = output_path.read_text(encoding="utf-8")

    assert "# Performance Baseline Report" in report_text
    assert "health_check" in report_text
    assert "http://localhost:8000" in report_text