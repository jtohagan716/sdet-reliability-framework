from framework.reliability.canary_history import CanaryHistory
from framework.reliability.canary_trend_analyzer import analyze_canary_trend


def test_canary_trend_insufficient_data():
    history = CanaryHistory()
    history.add_result(300)

    result = analyze_canary_trend(history)

    assert result["trend"] == "INSUFFICIENT_DATA"


def test_canary_trend_stable():
    history = CanaryHistory()
    history.add_result(300)
    history.add_result(295)

    result = analyze_canary_trend(history)

    assert result["trend"] == "IMPROVING_OR_STABLE"


def test_canary_trend_watch():
    history = CanaryHistory()
    history.add_result(300)
    history.add_result(360)

    result = analyze_canary_trend(history)

    assert result["trend"] == "WATCH"


def test_canary_trend_degrading():
    history = CanaryHistory()
    history.add_result(300)
    history.add_result(450)

    result = analyze_canary_trend(history)

    assert result["trend"] == "DEGRADING"
    assert "Investigate" in result["recommendation"]