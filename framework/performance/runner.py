from framework.performance.api_latency import measure_api_latency

from framework.reliability.trend_analyzer import (
detect_regression,
detect_p95_regression,
get_baseline,
get_trend,
)

from framework.reliability.reliability_score import (
calculate_reliability_score,
)

from framework.reliability.release_risk import (
calculate_release_risk,
)

from framework.reliability.release_decision import (
evaluate_release,
)

def run_performance_suite(
url: str,
iterations: int,
threshold_ms: int,
):


    print(
    f"[PERF START] {url} | "
    f"iterations={iterations} | "
    f"threshold={threshold_ms}ms"
)

    # ==================================================
    # PERFORMANCE COLLECTION
    # ==================================================

    result = measure_api_latency(url, iterations)

    avg = result["avg_ms"]
    p95 = result["p95_ms"]

    # ==================================================
    # REGRESSION ANALYSIS
    # ==================================================

    regression = detect_regression(avg)

    p95_regression = detect_p95_regression(p95)

    baseline = get_baseline()

    result["regression"] = regression["status"]
    result["baseline"] = baseline
    result["allowed_max"] = regression.get("allowed_max")

    result["p95_regression"] = p95_regression["status"]

    # ==================================================
    # TREND ANALYSIS
    # ==================================================

    trend = get_trend()

    result["trend"] = trend

    # ==================================================
    # DECISION ENGINE
    # ==================================================

    status = "PASS"

    if regression["status"] == "REGRESSION":
        status = "FAIL_BASELINE"

    elif trend == "DEGRADING":
        status = "FAIL_TREND"

    elif result["stdev_ms"] > (avg * 0.20):
        status = "FAIL_STABILITY"

    result["status"] = status

    # ==================================================
    # RELIABILITY SCORE
    # ==================================================

    reliability = calculate_reliability_score(result)

    result["reliability_score"] = reliability["score"]
    result["verdict"] = reliability["verdict"]
    result["score_breakdown"] = reliability["breakdown"]

    # ==================================================
    # RELEASE RISK
    # ==================================================

    risk = calculate_release_risk(result)

    result["risk_level"] = risk["risk_level"]
    result["risk_points"] = risk["risk_points"]

    # ==================================================
    # RELEASE DECISION
    # ==================================================

    release = evaluate_release(result)

    result["release_decision"] = release["decision"]
    result["release_reason"] = release["reason"]

    # ==================================================
    # PERFORMANCE REPORT
    # ==================================================

    print("\n=== PERFORMANCE INTELLIGENCE REPORT ===")

    print(f"Avg latency: {result['avg_ms']} ms")
    print(f"P50 latency: {result['p50_ms']} ms")
    print(f"P95 latency: {result['p95_ms']} ms")
    print(f"P99 latency: {result['p99_ms']} ms")

    print(f"Stdev: {result['stdev_ms']} ms")

    print(f"Baseline: {baseline}")
    print(f"Trend: {trend}")

    print(f"Regression Status: {regression['status']}")
    print(f"P95 Regression Status: {p95_regression['status']}")

    print(f"Final Decision: {status}")

    # ==================================================
    # BASELINE REPORT
    # ==================================================

    print("\nBASELINE CHECK")

    print(f"Allowed Max: {regression.get('allowed_max')}")
    print(f"Baseline: {baseline}")

    # ==================================================
    # RELIABILITY SCORE REPORT
    # ==================================================

    print("\n=== RELIABILITY SCORE ===")

    print(
        f"Score: {result['reliability_score']}/100"
    )

    print(
        f"Verdict: {result['verdict']}"
    )

    print(
        f"Breakdown: {result['score_breakdown']}"
    )

    # ==================================================
    # RELEASE RISK REPORT
    # ==================================================

    print("\n=== RELEASE RISK ===")

    print(
        f"Risk Level: {result['risk_level']}"
    )

    print(
        f"Risk Points: {result['risk_points']}"
    )

    # ==================================================
    # RELEASE DECISION REPORT
    # ==================================================

    print("\n=== RELEASE DECISION ===")

    print(
        f"Decision: {result['release_decision']}"
    )

    print(
        f"Reason: {result['release_reason']}"
    )

    print("[PERF END]")

    return result
   
