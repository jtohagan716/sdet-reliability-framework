def evaluate_transaction_variant(variant, observed_ms: float) -> dict:
    baseline = variant.baseline_ms

    difference_ms = observed_ms - baseline
    percent_over_baseline = (difference_ms / baseline) * 100

    if observed_ms <= baseline:
        status = "HEALTHY"
    elif percent_over_baseline <= 25:
        status = "WATCH"
    elif percent_over_baseline <= 50:
        status = "DEGRADED"
    else:
        status = "SEVERELY_DEGRADED"

    return {
        "variant": variant.name,
        "workload_profile": variant.workload_profile,
        "baseline_ms": baseline,
        "observed_ms": observed_ms,
        "difference_ms": round(difference_ms, 2),
        "percent_over_baseline": round(percent_over_baseline, 2),
        "status": status,
    }