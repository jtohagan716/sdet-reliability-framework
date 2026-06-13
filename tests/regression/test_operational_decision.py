from framework.reliability.operational_decision import make_operational_decision


def test_operational_decision_healthy():
    result = make_operational_decision({"health": "HEALTHY"})

    assert result["decision"] == "CONTINUE_MONITORING"
    assert result["severity"] == "NONE"


def test_operational_decision_watch():
    result = make_operational_decision({"health": "WATCH"})

    assert result["decision"] == "MONITOR_CLOSELY"
    assert result["severity"] == "LOW"


def test_operational_decision_degraded():
    result = make_operational_decision({"health": "DEGRADED"})

    assert result["decision"] == "INVESTIGATE"
    assert result["severity"] == "MEDIUM"


def test_operational_decision_unknown():
    result = make_operational_decision({"health": "UNKNOWN"})

    assert result["decision"] == "COLLECT_MORE_EVIDENCE"