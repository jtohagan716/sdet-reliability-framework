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
        "p95": result.get("p95_ms"),
        "p99": result.get("p99_ms"),
        "status": result.get("status"),
    })

    print("\n=== CI PERFORMANCE GATE ===")
    print(f"Reliability Score: {score}")
    print(f"CI Trend: {memory_trend['trend']}")
    print(f"CI Baseline: {memory_trend.get('baseline')}")

    # -----------------------------
    # FAILURE RULES
    # -----------------------------
     # -----------------------------
    # FAILURE RULES
    # -----------------------------
    if score < 70:
        print("\nCI FAILED: Reliability score below minimum threshold")
        raise SystemExit(1)

    if memory_trend["trend"] == "DEGRADING" and score < 80:
        print("\nCI FAILED: CI performance is degrading and reliability score is below warning threshold")
        raise SystemExit(1)

    if memory_trend["trend"] == "DEGRADING":
        print("\nCI WARNING: CI performance trend is degrading, but reliability score remains acceptable")
        print("\nCI GATE PASSED WITH WARNING")
        return

    print("\nCI GATE PASSED")
    sys.exit(0)
    
if __name__ == "__main__":
    main()