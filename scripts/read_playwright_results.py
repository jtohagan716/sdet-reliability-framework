import json
from pathlib import Path
from typing import Any


def read_json_file(path: Path) -> dict[str, Any]:
    for encoding in ("utf-8-sig", "utf-16", "utf-8"):
        try:
            return json.loads(path.read_text(encoding=encoding))
        except (UnicodeError, json.JSONDecodeError):
            continue

    raise ValueError(f"Unable to read JSON results file: {path}")


def count_failed_tests(suites: list[dict[str, Any]]) -> int:
    failures = 0

    for suite in suites:
        for spec in suite.get("specs", []):
            for test in spec.get("tests", []):
                for result in test.get("results", []):
                    if result.get("status") != "passed":
                        failures += 1

        failures += count_failed_tests(suite.get("suites", []))

    return failures


def count_total_tests(suites: list[dict[str, Any]]) -> int:
    total = 0

    for suite in suites:
        for spec in suite.get("specs", []):
            total += len(spec.get("tests", []))

        total += count_total_tests(suite.get("suites", []))

    return total


def get_playwright_status(
    results_file: str = "reports/playwright_observability_results.json",
) -> tuple[str, str]:
    path = Path(results_file)

    if not path.exists():
        return "Playwright Observability Tests", "FAIL"

    try:
        data = read_json_file(path)
    except ValueError:
        return "Playwright Observability Tests", "FAIL"

    suites = data.get("suites", [])
    total_tests = count_total_tests(suites)
    failed_tests = count_failed_tests(suites)

    if total_tests > 0 and failed_tests == 0:
        return "Playwright Observability Tests", "PASS"

    return "Playwright Observability Tests", "FAIL"


if __name__ == "__main__":
    name, status = get_playwright_status()
    print(f"{name:<35} {status}")