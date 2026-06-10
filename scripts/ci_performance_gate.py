import sys

from framework.performance.runner import run_performance_suite
from framework.reliability.ci_memory import save_run, detect_ci_trend


def main():
    url = "https://example.com"
    iterations = 8
    threshold = 3000

    result = run_performance_suite(url, iterations, threshold)

    score = result.get("reliability_score", 0)

    # -----------------------------
    # CI MEMORY LAYER (NEW)
    # -----------------------------
    memory_trend = detect_ci_trend(score)
    result["ci_trend"] = memory_trend["trend"]
    result["ci_baseline"] = memory_trend.get("baseline")

    # Save run to history
    save_run({
        "reliability_score": score,
        "avg_ms": result.get("avg_ms"),
        "p95": result.get("p95"),
        "p99": result.get("p99"),
        "status": result.get("status"),
    })

    print("\n=== CI PERFORMANCE GATE ===")
    print(f"Reliability Score: {score}")
    print(f"CI Trend: {memory_trend['trend']}")
    print(f"CI Baseline: {memory_trend.get('baseline')}")

    # -----------------------------
    # FAILURE RULES
    # -----------------------------
    if score < 70:
        print("\nCI FAILED: Low reliability score")
        sys.exit(1)

    if memory_trend["trend"] == "DEGRADING":
        print("\nCI FAILED: CI performance is degrading over time")
        sys.exit(1)

    if result.get("regression") == "REGRESSION":
        print("\nCI FAILED: Performance regression detected")
        sys.exit(1)

    print("\nCI GATE PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()