def make_operational_decision(health_result: dict) -> dict:
    health = health_result["health"]

    if health == "HEALTHY":
        return {
            "decision": "CONTINUE_MONITORING",
            "severity": "NONE",
            "action": "No operational action required.",
        }

    if health == "WATCH":
        return {
            "decision": "MONITOR_CLOSELY",
            "severity": "LOW",
            "action": "Continue monitoring and review next synthetic transaction run.",
        }

    if health == "DEGRADED":
        return {
            "decision": "INVESTIGATE",
            "severity": "MEDIUM",
            "action": "Begin investigation using canary history, timeline, and dependency graph.",
        }

    return {
        "decision": "COLLECT_MORE_EVIDENCE",
        "severity": "UNKNOWN",
        "action": "Collect additional synthetic transaction data before escalating.",
    }