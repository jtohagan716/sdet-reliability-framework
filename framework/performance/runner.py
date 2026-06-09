from framework.performance.api_latency import measure_api_latency
from framework.reliability.trend_analyzer import detect_regression


def run_performance_suite(url: str, iterations: int, threshold_ms: int):

    print(f"[PERF START] {url} | iterations={iterations} | threshold={threshold_ms}ms")

    result = measure_api_latency(url, iterations)

    regression = detect_regression(result["avg_ms"])

    result["regression"] = regression["status"]
    result["baseline"] = regression.get("baseline")
    result["allowed_max"] = regression.get("allowed_max")

    # Final status logic
    if regression["status"] == "REGRESSION":
        result["status"] = "FAIL_BASELINE"
    else:
        result["status"] = result.get("status", "PASS")

    print(f"[RESULT] {result}")
    print("\nBASELINE CHECK")
    print(f"Status: {result['regression']}")
    print(f"Baseline: {result.get('baseline')}")
    print(f"Allowed Max: {result.get('allowed_max')}")

    print("[PERF END]")

    return result