import json
from pathlib import Path
from typing import Any
from scripts.quality_signal import QualitySignal


def read_json_file(path: Path) -> dict[str, Any]:
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except (UnicodeError, json.JSONDecodeError):
            continue

    raise ValueError(f"Unable to read JSON results file: {path}")


def collect_test_counts(suites: list[dict[str, Any]]) -> tuple[int, int, int]:
    total = 0
    failed = 0

    for suite in suites:
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                total += 1

                results = test.get("results", [])
                test_passed = any(result.get("status") == "passed" for result in results)

                if not test_passed:
                    failed += 1

        child_total, child_failed, _ = collect_test_counts(suite.get("suites", []))
        total += child_total
        failed += child_failed

    passed = total - failed
    return total, failed, passed


def get_playwright_summary(
    results_file: str = "reports/playwright_observability_results.json",
) -> dict[str, int | str]:
    path = Path(results_file)

    if not path.exists():
        return {
            "name": "Playwright Observability Tests",
            "status": "FAIL",
            "total": 0,
            "passed": 0,
            "failed": 0,
        }

    try:
        data = read_json_file(path)
    except ValueError:
        return {
            "name": "Playwright Observability Tests",
            "status": "FAIL",
            "total": 0,
            "passed": 0,
            "failed": 0,
        }

    total, failed, passed = collect_test_counts(data.get("suites", []))
    status = "PASS" if total > 0 and failed == 0 else "FAIL"

    return {
        "name": "Playwright Observability Tests",
        "status": status,
        "total": total,
        "passed": passed,
        "failed": failed,
    }


def get_playwright_status(
    results_file: str = "reports/playwright_observability_results.json",
) -> tuple[str, str]:
    summary = get_playwright_summary(results_file)
    return str(summary["name"]), str(summary["status"])

def get_playwright_quality_signal(
    results_file: str = "reports/playwright_observability_results.json",
) -> QualitySignal:
    summary = get_playwright_summary(results_file)

    return QualitySignal(
        name=str(summary["name"]),
        status=str(summary["status"]),
        category="Automation",
        total=int(summary["total"]),
        passed=int(summary["passed"]),
        failed=int(summary["failed"]),
    )

if __name__ == "__main__":
    summary = get_playwright_summary()

    print(f"{summary['name']}")
    print("-" * 40)
    print(f"Total Tests : {summary['total']}")
    print(f"Passed      : {summary['passed']}")
    print(f"Failed      : {summary['failed']}")
    print(f"Status      : {summary['status']}")