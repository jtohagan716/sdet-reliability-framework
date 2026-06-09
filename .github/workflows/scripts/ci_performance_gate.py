from framework.performance.runner import run_performance_suite
import sys


def main():
    result = run_performance_suite(
        "https://example.com",
        iterations=5,
        threshold_ms=3000
    )

    print("\nCI PERFORMANCE GATE RESULT")
    print(result)

    status = result.get("status")

    if status in ["REGRESSION", "SEVERE_REGRESSION"]:
        print("CI FAIL: Performance regression detected")
        sys.exit(1)

    print("CI PASS: Performance within acceptable bounds")
    sys.exit(0)


if __name__ == "__main__":
    main()