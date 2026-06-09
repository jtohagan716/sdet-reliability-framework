from framework.reliability.reliability_score import calculate_reliability_score
from framework.performance.api_latency import measure_api_latency
from framework.reliability.trend_analyzer import (
    detect_regression,
    get_trend,
    get_baseline,
    detect_p95_regression,
)


def run_performance_suite(url: str, iterations: int, threshold_ms: int):

    print(
        f"[PERF START] {url} | "
        f"iterations={iterations} | "
        f"threshold={threshold_ms}ms"
    )

    # -----------------------------
    # 1. COLLECT PERFORMANCE DATA
    # -----------------------------
    result = measure_api_latency(url, iterations)

    avg = result["avg_ms"]
    p95 = result["p95_ms"]

    # -----------------------------
    # 2. BASELINE + REGRESSION CHECK
    # -----------------------------
    regression = detect_regression(avg)
    baseline = get_baseline()

    result["regression"] = regression["status"]
    result["baseline"] = baseline
    result["allowed_max"] = regression.get("allowed_max")

    # -----------------------------
    # 3. P95 REGRESSION CHECK (TAIL LATENCY)
    # -----------------------------
    p95_regression = detect_p95_regression(p95)
    result["p95_regression"] = p95_regression["status"]

    # -----------------------------
    # 4. TREND ANALYSIS
    # -----------------------------
    trend = get_trend()
    result["trend"] = trend
    # -----------------------------
    # RELIABILITY SCORE ENGINE
    # -----------------------------
    reliability = calculate_reliability_score(result, trend)

    result["reliability_score"] = reliability.score
    result["verdict"] = reliability.verdict
    result["score_breakdown"] = reliability.breakdown



    # -----------------------------
    # 5. INTELLIGENCE DECISION ENGINE
    # -----------------------------
    status = "PASS"

    if regression["status"] == "REGRESSION":
        status = "FAIL_BASELINE"

    elif p95_regression["status"] == "REGRESSION":
        status = "FAIL_TAIL"

    elif trend == "DEGRADING":
        status = "FAIL_TREND"

    elif result["stdev_ms"] > (avg * 0.2):
        status = "FAIL_STABILITY"

    result["status"] = status

    # -----------------------------
    # 6. PERFORMANCE INTELLIGENCE REPORT
    # -----------------------------
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

    # -----------------------------
    # 7. BASELINE CONTEXT OUTPUT
    # -----------------------------
    print("\nBASELINE CHECK")
    print(f"Allowed Max: {regression.get('allowed_max')}")
    print(f"Baseline: {baseline}")

    print("\n=== RELIABILITY SCORE ===")
    print(f"Score: {reliability.score}/100")
    print(f"Verdict: {reliability.verdict}")
    print(f"Breakdown: {reliability.breakdown}")

    print("[PERF END]")

    return result