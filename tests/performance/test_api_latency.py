from types import SimpleNamespace

import framework.performance.runner as performance_runner


def test_api_latency_pipeline_contract(monkeypatch):
    def fake_measure_api_latency(
        url: str,
        iterations: int,
    ) -> dict[str, object]:
        return {
            "url": url,
            "iterations": iterations,
            "min_ms": 80.0,
            "max_ms": 120.0,
            "avg_ms": 100.0,
            "stdev_ms": 5.0,
            "p50_ms": 98.0,
            "p95_ms": 115.0,
            "p99_ms": 119.0,
        }

    monkeypatch.setattr(
        performance_runner,
        "measure_api_latency",
        fake_measure_api_latency,
    )

    monkeypatch.setattr(
        performance_runner,
        "detect_regression",
        lambda average_ms: {
            "status": "STABLE",
            "allowed_max": 125.0,
        },
    )

    monkeypatch.setattr(
        performance_runner,
        "detect_p95_regression",
        lambda p95_ms: {
            "status": "STABLE",
        },
    )

    monkeypatch.setattr(
        performance_runner,
        "get_baseline",
        lambda: 100.0,
    )

    monkeypatch.setattr(
        performance_runner,
        "get_trend",
        lambda: "STABLE",
    )

    monkeypatch.setattr(
        performance_runner,
        "calculate_reliability_score",
        lambda result, trend: SimpleNamespace(
            score=96.0,
            verdict="RELIABLE",
            breakdown={
                "latency": 40,
                "stability": 30,
                "trend": 26,
            },
        ),
    )

    monkeypatch.setattr(
        performance_runner,
        "calculate_release_risk",
        lambda result: {
            "risk_level": "LOW",
            "risk_points": 0,
        },
    )

    monkeypatch.setattr(
        performance_runner,
        "evaluate_release",
        lambda result: {
            "decision": "GO",
            "reason": "Deterministic test conditions passed.",
        },
    )

    result = performance_runner.run_performance_suite(
        "http://local.test/health",
        iterations=8,
        threshold_ms=250,
    )

    assert result["url"] == "http://local.test/health"
    assert result["iterations"] == 8

    assert result["avg_ms"] == 100.0
    assert result["stdev_ms"] == 5.0
    assert result["p50_ms"] == 98.0
    assert result["p95_ms"] == 115.0
    assert result["p99_ms"] == 119.0

    assert result["regression"] == "STABLE"
    assert result["p95_regression"] == "STABLE"
    assert result["baseline"] == 100.0
    assert result["allowed_max"] == 125.0
    assert result["trend"] == "STABLE"
    assert result["status"] == "PASS"

    assert result["reliability_score"] == 96.0
    assert result["verdict"] == "RELIABLE"
    assert result["risk_level"] == "LOW"
    assert result["risk_points"] == 0
    assert result["release_decision"] == "GO"
    assert (
        result["release_reason"]
        == "Deterministic test conditions passed."
    )
