import argparse
import math
import random
import statistics
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class LoadScenario:
    name: str
    path: str
    expected_status: int
    weight: int


@dataclass(frozen=True)
class RequestResult:
    scenario: str
    path: str
    expected_status: int
    actual_status: int | None
    duration_ms: float
    passed: bool
    error: str | None = None


SCENARIOS = [
    LoadScenario(
        name="patient_lookup_primary_success",
        path="/patients/1001",
        expected_status=200,
        weight=60,
    ),
    LoadScenario(
        name="patient_lookup_secondary_success",
        path="/patients/1002",
        expected_status=200,
        weight=20,
    ),
    LoadScenario(
        name="patient_lookup_not_found",
        path="/patients/9999",
        expected_status=404,
        weight=10,
    ),
    LoadScenario(
        name="patient_lookup_invalid_id",
        path="/patients/abc",
        expected_status=422,
        weight=5,
    ),
    LoadScenario(
        name="health_check",
        path="/health",
        expected_status=200,
        weight=5,
    ),
]


def percentile(values: list[float], percent: float) -> float:
    if not values:
        return 0.0

    sorted_values = sorted(values)
    index = math.ceil((percent / 100) * len(sorted_values)) - 1
    index = max(0, min(index, len(sorted_values) - 1))

    return sorted_values[index]


def build_weighted_schedule(
    scenarios: list[LoadScenario],
    total_requests: int,
    seed: int,
) -> list[LoadScenario]:
    if total_requests <= 0:
        raise ValueError("total_requests must be greater than zero")

    total_weight = sum(scenario.weight for scenario in scenarios)

    allocations = []
    allocated_count = 0

    for scenario in scenarios:
        exact_count = (total_requests * scenario.weight) / total_weight
        base_count = int(exact_count)
        remainder = exact_count - base_count

        allocations.append(
            {
                "scenario": scenario,
                "count": base_count,
                "remainder": remainder,
            }
        )

        allocated_count += base_count

    remaining = total_requests - allocated_count

    allocations.sort(key=lambda item: item["remainder"], reverse=True)

    for allocation in allocations[:remaining]:
        allocation["count"] += 1

    schedule: list[LoadScenario] = []

    for allocation in allocations:
        schedule.extend([allocation["scenario"]] * allocation["count"])

    rng = random.Random(seed)
    rng.shuffle(schedule)

    return schedule


def call_endpoint(base_url: str, scenario: LoadScenario) -> RequestResult:
    url = f"{base_url.rstrip('/')}{scenario.path}"

    request = Request(
        url,
        headers={"X-Request-ID": f"loadtest-{uuid.uuid4()}"},
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

    except (URLError, TimeoutError) as error:
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


def summarize_results(
    results: list[RequestResult],
    elapsed_seconds: float,
) -> dict[str, object]:
    durations = [result.duration_ms for result in results]
    passed_count = sum(1 for result in results if result.passed)
    failed_count = len(results) - passed_count

    return {
        "total_requests": len(results),
        "passed": passed_count,
        "failed": failed_count,
        "error_rate_percent": round((failed_count / len(results)) * 100, 2),
        "avg_ms": round(statistics.mean(durations), 2),
        "min_ms": round(min(durations), 2),
        "max_ms": round(max(durations), 2),
        "p95_ms": round(percentile(durations, 95), 2),
        "p99_ms": round(percentile(durations, 99), 2),
        "elapsed_seconds": round(elapsed_seconds, 2),
        "requests_per_second": round(len(results) / elapsed_seconds, 2),
    }


def summarize_by_scenario(results: list[RequestResult]) -> list[dict[str, object]]:
    summaries = []

    for scenario in SCENARIOS:
        scenario_results = [
            result for result in results if result.scenario == scenario.name
        ]

        if not scenario_results:
            continue

        durations = [result.duration_ms for result in scenario_results]
        passed_count = sum(1 for result in scenario_results if result.passed)
        failed_count = len(scenario_results) - passed_count

        summaries.append(
            {
                "scenario": scenario.name,
                "path": scenario.path,
                "expected_status": scenario.expected_status,
                "weight": scenario.weight,
                "count": len(scenario_results),
                "passed": passed_count,
                "failed": failed_count,
                "error_rate_percent": round(
                    (failed_count / len(scenario_results)) * 100,
                    2,
                ),
                "avg_ms": round(statistics.mean(durations), 2),
                "min_ms": round(min(durations), 2),
                "max_ms": round(max(durations), 2),
                "p95_ms": round(percentile(durations, 95), 2),
            }
        )

    return summaries


def run_load_test(
    base_url: str,
    total_requests: int,
    concurrency: int,
    seed: int,
) -> tuple[list[RequestResult], float]:
    if concurrency <= 0:
        raise ValueError("concurrency must be greater than zero")

    schedule = build_weighted_schedule(
        scenarios=SCENARIOS,
        total_requests=total_requests,
        seed=seed,
    )

    results: list[RequestResult] = []

    start_time = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [
            executor.submit(call_endpoint, base_url, scenario)
            for scenario in schedule
        ]

        for future in as_completed(futures):
            results.append(future.result())

    elapsed_seconds = time.perf_counter() - start_time

    return results, elapsed_seconds


def write_markdown_report(
    output_path: Path,
    base_url: str,
    total_requests: int,
    concurrency: int,
    seed: int,
    overall_summary: dict[str, object],
    scenario_summaries: list[dict[str, object]],
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    generated_at = datetime.now(UTC).isoformat()

    lines = [
        "# Lightweight Load Test Report",
        "",
        f"Generated UTC: `{generated_at}`",
        f"Base URL: `{base_url}`",
        f"Total Requests: `{total_requests}`",
        f"Concurrency: `{concurrency}`",
        f"Traffic Seed: `{seed}`",
        "",
        "## Overall Summary",
        "",
        "| Total Requests | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms | P99 ms | Elapsed sec | Requests/sec |",
        "|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
        "| {total_requests} | {passed} | {failed} | {error_rate_percent} | {avg_ms} | {min_ms} | {max_ms} | {p95_ms} | {p99_ms} | {elapsed_seconds} | {requests_per_second} |".format(
            **overall_summary
        ),
        "",
        "## Scenario Breakdown",
        "",
        "| Scenario | Path | Expected Status | Weight | Count | Passed | Failed | Error Rate % | Avg ms | Min ms | Max ms | P95 ms |",
        "|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for summary in scenario_summaries:
        lines.append(
            "| {scenario} | `{path}` | {expected_status} | {weight} | {count} | {passed} | {failed} | {error_rate_percent} | {avg_ms} | {min_ms} | {max_ms} | {p95_ms} |".format(
                **summary
            )
        )

    lines.extend(
        [
            "",
            "## Interpretation",
            "",
            "This report captures a lightweight local load test using a weighted traffic mix.",
            "",
            "- `passed` means the endpoint returned the expected HTTP status code.",
            "- `failed` means the endpoint returned an unexpected status code or could not be reached.",
            "- `404` and `422` can be passing results when they are the expected behavior for the scenario.",
            "- `p95_ms` shows the approximate 95th percentile response time.",
            "- `requests_per_second` shows observed local throughput during the run.",
            "",
            "## Reliability Value",
            "",
            "This load test provides evidence about API behavior under a small controlled traffic mix. It helps compare expected behavior, response time, error rate, and throughput against the previous baseline.",
            "",
        ]
    )

    output_path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a lightweight local API load test."
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL for the API under test.",
    )
    parser.add_argument(
        "--total-requests",
        type=int,
        default=100,
        help="Total number of requests to send.",
    )
    parser.add_argument(
        "--concurrency",
        type=int,
        default=5,
        help="Number of concurrent worker threads.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Random seed used to shuffle the weighted traffic schedule.",
    )
    parser.add_argument(
        "--output",
        default="reports/lightweight_load_test_v0.7.0.md",
        help="Markdown report output path.",
    )

    args = parser.parse_args()

    results, elapsed_seconds = run_load_test(
        base_url=args.base_url,
        total_requests=args.total_requests,
        concurrency=args.concurrency,
        seed=args.seed,
    )

    overall_summary = summarize_results(results, elapsed_seconds)
    scenario_summaries = summarize_by_scenario(results)

    output_path = Path(args.output)

    write_markdown_report(
        output_path=output_path,
        base_url=args.base_url,
        total_requests=args.total_requests,
        concurrency=args.concurrency,
        seed=args.seed,
        overall_summary=overall_summary,
        scenario_summaries=scenario_summaries,
    )

    print(f"Lightweight load test report written to: {output_path}")
    print(
        "total_requests={total_requests}, passed={passed}, failed={failed}, error_rate={error_rate_percent}%, avg_ms={avg_ms}, p95_ms={p95_ms}, p99_ms={p99_ms}, requests_per_second={requests_per_second}".format(
            **overall_summary
        )
    )

    if overall_summary["failed"]:
        print(f"Unexpected failures detected: {overall_summary['failed']}")
        return 1

    print("Lightweight load test completed successfully.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())