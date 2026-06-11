def evaluate_transaction_variant(variant, observed_ms: float) -> dict:
    baseline = variant.baseline_ms

    difference_ms = observed_ms - baseline
    percent_over_baseline = (difference_ms / baseline) * 100

    if observed_ms <= baseline:
        status = "HEALTHY"
        recommendation = "No action required."

    elif percent_over_baseline <= 25:
        status = "WATCH"
        recommendation = (
            "Monitor for repeat occurrence and compare against recent trend data."
        )

    elif percent_over_baseline <= 50:
        status = "DEGRADED"
        recommendation = (
            "Investigate transaction dependency timing and compare against roadmap phases."
        )

    else:
        status = "SEVERELY_DEGRADED"
        recommendation = (
            "Escalate for immediate review. Check service dependencies, database timing, "
            "middleware behavior, and infrastructure capacity."
        )

    return {
        "variant": variant.name,
        "workload_profile": variant.workload_profile,
        "baseline_ms": baseline,
        "observed_ms": observed_ms,
        "difference_ms": round(difference_ms, 2),
        "percent_over_baseline": round(percent_over_baseline, 2),
        "status": status,
        "recommendation": recommendation,
    }