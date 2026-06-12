def analyze_canary_trend(history):
    durations = history.durations

    if len(durations) < 2:
        return {
            "trend": "INSUFFICIENT_DATA",
            "recommendation": "Collect more canary executions before evaluating trend.",
        }

    first = durations[0]
    latest = durations[-1]

    if latest <= first:
        trend = "IMPROVING_OR_STABLE"
        recommendation = "Canary performance is stable or improving."

    elif latest <= first * 1.25:
        trend = "WATCH"
        recommendation = "Canary performance has increased slightly. Continue monitoring."

    else:
        trend = "DEGRADING"
        recommendation = "Canary performance is degrading. Investigate recent changes or dependency latency."

    return {
        "first_duration_ms": first,
        "latest_duration_ms": latest,
        "trend": trend,
        "recommendation": recommendation,
    }