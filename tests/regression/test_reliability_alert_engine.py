from framework.reliability.reliability_alert_engine import (
    ReliabilityAlertEngine,
)


def test_alert_engine_no_alert():

    engine = ReliabilityAlertEngine()

    result = engine.evaluate_dashboard(
        {
            "health_counts": {
                "HEALTHY": 5
            }
        }
    )

    assert result["alert"] is False


def test_alert_engine_generates_alert():

    engine = ReliabilityAlertEngine()

    result = engine.evaluate_dashboard(
        {
            "health_counts": {
                "HEALTHY": 4,
                "DEGRADED": 1,
            }
        }
    )

    assert result["alert"] is True
    assert result["severity"] == "HIGH"