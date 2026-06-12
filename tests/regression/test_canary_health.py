from framework.reliability.canary_health import classify_canary_health


def test_canary_health_healthy():

    result = classify_canary_health({
        "trend": "IMPROVING_OR_STABLE"
    })

    assert result["health"] == "HEALTHY"


def test_canary_health_watch():

    result = classify_canary_health({
        "trend": "WATCH"
    })

    assert result["health"] == "WATCH"


def test_canary_health_degraded():

    result = classify_canary_health({
        "trend": "DEGRADING"
    })

    assert result["health"] == "DEGRADED"


def test_canary_health_unknown():

    result = classify_canary_health({
        "trend": "INSUFFICIENT_DATA"
    })

    assert result["health"] == "UNKNOWN"