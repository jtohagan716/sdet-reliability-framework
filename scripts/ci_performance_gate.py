import sys
import os

# 🔥 Force repo root onto Python path (CI-safe)
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from framework.performance.runner import run_performance_suite
import sys as system_exit


def main():
    result = run_performance_suite(
        "https://example.com",
        iterations=5,
        threshold_ms=3000
    )

    print("\nCI PERFORMANCE GATE RESULT")
    print(result)

    status = result.get("status")

    if status in ["REGRESSION", "SEVERE_REGRESSION", "FAIL_STABILITY", "FAIL_TREND"]:
        print("CI FAIL: Performance regression detected")
        system_exit.exit(1)

    print("CI PASS: Performance within acceptable bounds")
    system_exit.exit(0)


if __name__ == "__main__":
    main()