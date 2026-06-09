import sys

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
    # FAILURE CONDITIONS
    # -----------------------------
    if score < 70:
        print("\nCI FAILED: Low reliability score")
        sys.exit(1)

    if result.get("regression") == "REGRESSION":
        print("\nCI FAILED: Performance regression detected")
        sys.exit(1)

    if result.get("trend") == "DEGRADING":
        print("\nCI FAILED: Negative performance trend")
        sys.exit(1)

    print("\nCI GATE PASSED")
    sys.exit(0)


if __name__ == "__main__":
    main()