from collections import Counter
from pathlib import Path

from scripts.run_lightweight_load_test import (
    RequestResult,
    SCENARIOS,
    build_weighted_schedule,
    percentile,
    summarize_by_scenario,
    summarize_results,
    write_markdown_report,
)


def test_percentile_returns_expected_nearest_rank_value():
    values = [10.0, 20.0, 30.0, 40.0, 50.0]

    assert percentile(values, 95) == 50.0


def test_build_weighted_schedule_preserves_expected_distribution():
    schedule = build_weighted_schedule(
        scenarios=SCENARIOS,
        total_requests=100,
        seed=7,
    )

    scenario_counts = Counter(scenario.name for scenario in schedule)

    assert len(schedule) == 100
    assert scenario_counts["patient_lookup_primary_success"] == 60
    assert scenario_counts["patient_lookup_secondary_success"] == 20
    assert scenario_counts["patient_lookup_not_found"] == 10
    assert scenario_counts["patient_lookup_invalid_id"] == 5
    assert scenario_counts["health_check"] == 5


def test_summarize_results_reports_overall_load_test_metrics():
    results = [
        RequestResult(
            scenario="patient_lookup_primary_success",
            path="/patients/1001",
            expected_status=200,
            actual_status=200,
            duration_ms=10.0,
            passed=True,
        ),
        RequestResult(
            scenario="patient_lookup_secondary_success",
            path="/patients/1002",
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
        RequestResult(
            scenario="patient_lookup_invalid_id",
            path="/patients/abc",
            expected_status=422,
            actual_status=422,
            duration_ms=40.0,
            passed=True,
        ),
    ]

    summary = summarize_results(results, elapsed_seconds=2.0)

    assert summary["total_requests"] == 4
    assert summary["passed"] == 4
    assert summary["failed"] == 0
    assert summary["error_rate_percent"] == 0.0
    assert summary["avg_ms"] == 25.0
    assert summary["min_ms"] == 10.0
    assert summary["max_ms"] == 40.0
    assert summary["requests_per_second"] == 2.0


def test_summarize_by_scenario_reports_expected_status_outcomes():
    results = [
        RequestResult(
            scenario="patient_lookup_primary_success",
            path="/patients/1001",
            expected_status=200,
            actual_status=200,
            duration_ms=10.0,
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

    summaries = summarize_by_scenario(results)

    assert len(summaries) == 2

    primary_summary = next(
        summary
        for summary in summaries
        if summary["scenario"] == "patient_lookup_primary_success"
    )

    not_found_summary = next(
        summary
        for summary in summaries
        if summary["scenario"] == "patient_lookup_not_found"
    )

    assert primary_summary["path"] == "/patients/1001"
    assert primary_summary["expected_status"] == 200
    assert primary_summary["passed"] == 1
    assert primary_summary["failed"] == 0

    assert not_found_summary["path"] == "/patients/9999"
    assert not_found_summary["expected_status"] == 404
    assert not_found_summary["passed"] == 1
    assert not_found_summary["failed"] == 0


def test_write_markdown_report_creates_expected_load_test_report(tmp_path):
    output_path = tmp_path / "lightweight_load_test.md"

    overall_summary = {
        "total_requests": 100,
        "passed": 100,
        "failed": 0,
        "error_rate_percent": 0.0,
        "avg_ms": 25.0,
        "min_ms": 10.0,
        "max_ms": 40.0,
        "p95_ms": 40.0,
        "p99_ms": 40.0,
        "elapsed_seconds": 2.0,
        "requests_per_second": 50.0,
    }

    scenario_summaries = [
        {
            "scenario": "patient_lookup_primary_success",
            "path": "/patients/1001",
            "expected_status": 200,
            "weight": 60,
            "count": 60,
            "passed": 60,
            "failed": 0,
            "error_rate_percent": 0.0,
            "avg_ms": 25.0,
            "min_ms": 10.0,
            "max_ms": 40.0,
            "p95_ms": 40.0,
        }
    ]

    write_markdown_report(
        output_path=Path(output_path),
        base_url="http://localhost:8000",
        total_requests=100,
        concurrency=5,
        seed=7,
        overall_summary=overall_summary,
        scenario_summaries=scenario_summaries,
    )

    report_text = output_path.read_text(encoding="utf-8")

    assert "# Lightweight Load Test Report" in report_text
    assert "patient_lookup_primary_success" in report_text
    assert "/patients/1001" in report_text
    assert "Requests/sec" in report_text