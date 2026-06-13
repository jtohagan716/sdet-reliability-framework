from framework.reliability.reliability_trend_reporter import (
    ReliabilityTrendReporter,
)


def test_reliability_trend_reporter():

    reporter = ReliabilityTrendReporter()

    report = reporter.generate(
        [
            {
                "duration_ms": 300,
            },
            {
                "duration_ms": 350,
            },
            {
                "duration_ms": 400,
            },
        ]
    )

    assert report["count"] == 3
    assert report["average_latency"] == 350
    assert report["latest_latency"] == 400
    assert report["trend"] == "DEGRADING"