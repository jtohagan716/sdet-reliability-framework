import sys
import json

from framework.performance.runner import run_performance_suite


def main():
    url = "https://example.com"
    iterations = 8
    threshold = 3000

    result = run_performance_suite(url, iterations, threshold)

    score = result.get("reliability_score", 0)
    verdict = result.get("verdict", "UNKNOWN")

    print("\n=== CI PERFORMANCE GATE ===")
    print(f"Reliability Score: {score}")
    print(f"Verdict: {verdict}")

    # -----------------------------
    # CI FAILURE CONDITIONS
    # -----------------------------
    if score < 70:
        print("\n❌ FAILED: Reliability score too low")
        sys.exit(1)

    if result.get("regression") == "REGRESSION":
        print("\n❌ FAILED: Performance regression detected")
        sys.exit(1)

    if result.get("trend") == "DEGRADING":
        print("\n❌ FAILED: Negative performance trend")
        sys.exit(1)

    print("\n✅ CI GATE PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()