import argparse
import statistics
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass
class EndpointScenario:
    name: str
    path: str
    expected_status: int


@dataclass
class RequestResult:
    scenario: str
    path: str
    expected_status: int
    actual_status: int | None
    duration_ms: float
    passed: bool
    error: str | None = None


SCENARIOS = [
    EndpointScenario(
        name="health_check",
        path="/health",
        expected_status=200,
    ),
    EndpointScenario(
        name="patient_lookup_success",
        path="/patients/1001",
        expected_status=200,
    ),
    EndpointScenario(
        name="patient_lookup_not_found",
        path="/patients/9999",
        expected_status=404,
    ),
]


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = round((len(sorted_values) - 1) * percent)
    return sorted_values[index]


def call_endpoint(base_url: str, scenario: EndpointScenario) -> RequestResult:
    url = f"{base_url.rstrip('/')}{scenario.path}"
    request = Request(
        url,
        headers={"X-Request-ID": f"baseline-{scenario.name}-{time.time_ns()}"},
        method="GET",
    )

    start_time = time.perf_counter()

    try:
        with urlopen(request, timeout=10) as response:
            response.read()
            actual_status = response.status

    except HTTPError as error:
        error.read()
        actual_status = error.code

    except URLError as error:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        return RequestResult(
            scenario=scenario.name,
            path=scenario.path,
            expected_status=scenario.expected_status,
            actual_status=None,
            duration_ms=duration_ms,
            passed=False,
            error=str(error),
        )

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)

    return RequestResult(
        scenario=scenario.name,
        path=scenario.path,
        expected_status=scenario.expected_status,
        actual_status=actual_status,
        duration_ms=duration_ms,
        passed=actual_status == scenario.expected_status,
    )


def summarize_results(results: list[RequestResult]) -> list[dict[str, object]]:
    summaries = []

    for scenario in SCENARIOS:
        scenario_results = [
            result for result in results if result.scenario == scenario.name
        ]

        durations = [result.duration_ms for result in scenario_results]
        passed_count = sum(1 for result in scenario_results if result.passed)
        failed_count = len(scenario_results) - passed_count
        error_rate = round((failed_count / len(scenario_results)) * 100, 2)

        summaries.append(
            {
                "scenario": scenario.name,
                "path": scenario.path,
                "expected_status": scenario.expected_status,
                "count": len(scenario_results),
                "passed": passed_count,
                "failed": failed_count,
                "error_rate_percent": error_rate,
                "avg_ms": round(statistics.mean(durations), 2),
                "min_ms": round(min(durations), 2),
                "max_ms": round(max(durations), 2),
                "p95_ms": round(percentile(durations, 0.95), 2),
            }
        )

    return summaries


def find_p95_threshold_failures(
    summaries: list[dict[str, object]],
    max_p95_ms: float,
) -> list[dict[str, object]]:
    return [
        summary
        for summary in summaries
        if float(summary["p95_ms"]) > max_p95_ms
    ]


def write_markdown_report(
    output_path: Path,
    base_url: str,
    iterations: int,
    summaries: list[dict[str, object]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(UTC).isoformat()

    lines = [
        "# Performance Baseline Report",
        "",
        f"Generated UTC: `{generated_at}`",
        f"Base URL: `{base_url}`",
        f"Iterations per scenario: `{iterations}`",
        "",
        "## Summary",
        "",
        "| Scenario | Path | Expected Status | Count | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for summary in summaries:
        lines.append(
            "| {scenario} | `{path}` | {expected_status} | {count} | {passed} | {failed} | {error_rate_percent} | {avg_ms} | {min_ms} | {max_ms} | {p95_ms} |".format(
                **summary
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report captures a local baseline for selected API paths.",
            "",
            "- `passed` means the endpoint returned the expected HTTP status code.",
            "- `failed` means the endpoint returned an unexpected result or could not be reached.",
            "- `p95_ms` represents the approximate 95th percentile response time for the scenario.",
            "- This is not a full load test. It is a repeatable local baseline used for comparison against future changes.",
            "",
            "## Reliability Value",
            "",
            "This baseline helps compare future behavior against a known-good local run. It supports performance regression detection, release-readiness review, and troubleshooting conversations.",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a local API performance baseline."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the API under test.",
    )
    parser.add_argument(
        "--iterations",
        type=int,
        default=10,
        help="Number of requests to send per scenario.",
    )
    parser.add_argument(
        "--max-p95-ms",
        type=float,
        default=1000.0,
        help="Maximum permitted p95 latency for each scenario.",
    )
    parser.add_argument(
        "--output",
        default="reports/performance_baseline_v0.6.0.md",
        help="Markdown report output path.",
    )

    args = parser.parse_args()

    if args.iterations < 1:
        parser.error(
            "--iterations must be greater than zero."
        )

    if args.max_p95_ms <= 0:
        parser.error(
            "--max-p95-ms must be greater than zero."
        )

    results: list[RequestResult] = []

    for _ in range(args.iterations):
        for scenario in SCENARIOS:
            results.append(call_endpoint(args.base_url, scenario))

    summaries = summarize_results(results)

    threshold_failures = find_p95_threshold_failures(
        summaries,
        args.max_p95_ms,
    )

    output_path = Path(args.output)
    write_markdown_report(output_path, args.base_url, args.iterations, summaries)

    print(f"Performance baseline report written to: {output_path}")

    unexpected_failures = sum(summary["failed"] for summary in summaries)

    for summary in summaries:
        print(
            "{scenario}: count={count}, passed={passed}, failed={failed}, avg_ms={avg_ms}, p95_ms={p95_ms}, error_rate={error_rate_percent}%".format(
                **summary
            )
        )

    if unexpected_failures:
        print(f"Unexpected failures detected: {unexpected_failures}")
        return 1

    if threshold_failures:
        print(
            "P95 latency threshold exceeded: "
            f"maximum permitted={args.max_p95_ms} ms"
        )

        for summary in threshold_failures:
            print(
                f"{summary['scenario']}: "
                f"p95={summary['p95_ms']} ms"
            )

        return 1

    print("Performance baseline completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())