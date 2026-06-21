def evaluate_latency(current_ms: int, baseline_ms: int) -> dict:
    ratio = current_ms / baseline_ms

    if ratio <= 1.5:
        status = "HEALTHY"
    elif ratio <= 3.0:
        status = "WATCH"
    else:
        status = "DEGRADED"

    return {
        "currentMs": current_ms,
        "baselineMs": baseline_ms,
        "ratio": round(ratio, 2),
        "status": status,
    }