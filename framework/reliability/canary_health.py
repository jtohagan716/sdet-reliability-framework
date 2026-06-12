def classify_canary_health(trend_result):

    trend = trend_result["trend"]

    if trend == "IMPROVING_OR_STABLE":
        health = "HEALTHY"
        recommendation = "No action required."

    elif trend == "WATCH":
        health = "WATCH"
        recommendation = "Continue monitoring synthetic transaction performance."

    elif trend == "DEGRADING":
        health = "DEGRADED"
        recommendation = "Investigate recent performance changes."

    else:
        health = "UNKNOWN"
        recommendation = "Collect additional synthetic transaction data."

    return {
        "health": health,
        "recommendation": recommendation,
    }