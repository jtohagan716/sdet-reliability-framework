from __future__ import annotations

import argparse
import csv
import json
import math
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIRECTORY = REPOSITORY_ROOT / "reports" / "test-runs"

API_BASE_URL = "http://localhost:8000"
TIMING_ENDPOINT = (
    f"{API_BASE_URL}/qa/database-connection-timing"
    "?patient_id=1001"
)

SUPPORTED_STRATEGIES = {
    "connection_per_operation",
    "bounded_pool",
}

DATABASE_PHASE_NAMES = (
    "acquire_ms",
    "query_ms",
    "fetch_ms",
    "release_ms",
    "total_ms",
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def utc_timestamp() -> str:
    return utc_now().isoformat()


def percentile(
    values: list[float],
    percent: int,
) -> float | None:
    if not values:
        return None

    ordered = sorted(values)
    rank = math.ceil((percent / 100) * len(ordered))
    index = max(0, min(len(ordered) - 1, rank - 1))

    return round(ordered[index], 3)


def metric_summary(
    values: list[float],
) -> dict[str, float | int | None]:
    if not values:
        return {
            "count": 0,
            "minimum_ms": None,
            "mean_ms": None,
            "p50_ms": None,
            "p95_ms": None,
            "p99_ms": None,
            "maximum_ms": None,
        }

    return {
        "count": len(values),
        "minimum_ms": round(min(values), 3),
        "mean_ms": round(sum(values) / len(values), 3),
        "p50_ms": percentile(values, 50),
        "p95_ms": percentile(values, 95),
        "p99_ms": percentile(values, 99),
        "maximum_ms": round(max(values), 3),
    }


def run_starting_state_preparation(
    *,
    mode: str,
    warmup_count: int,
    stabilization_seconds: float,
) -> tuple[str, Path, dict[str, Any]]:
    command = [
        sys.executable,
        "scripts/prepare_database_test_state.py",
        "--mode",
        mode,
        "--warmup-count",
        str(warmup_count),
        "--stabilization-seconds",
        str(stabilization_seconds),
    ]

    subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        check=True,
    )

    latest_path = (
        TEST_RUNS_DIRECTORY
        / "latest-starting-state-run.txt"
    )

    starting_state_run_id = latest_path.read_text(
        encoding="utf-8"
    ).strip()

    manifest_path = (
        TEST_RUNS_DIRECTORY
        / starting_state_run_id
        / "starting-state.json"
    )

    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8")
    )

    return starting_state_run_id, manifest_path, manifest


def validate_starting_state(
    manifest: dict[str, Any],
    expected_strategy: str,
) -> None:
    if not manifest.get("starting_state_valid"):
        raise RuntimeError(
            "Starting-state manifest is not marked valid"
        )

    actual_strategy = manifest["strategy"][
        "connection_strategy"
    ]

    if actual_strategy != expected_strategy:
        raise RuntimeError(
            "Starting-state strategy mismatch: "
            f"expected {expected_strategy!r}, "
            f"received {actual_strategy!r}"
        )

    idle_in_transaction = manifest[
        "database_after_warmup"
    ]["idle_in_transaction_count"]

    if idle_in_transaction != 0:
        raise RuntimeError(
            "Starting state contains idle-in-transaction "
            f"sessions: {idle_in_transaction}"
        )


def execute_worker(
    *,
    worker_number: int,
    requests_per_worker: int,
    strategy: str,
    run_id: str,
    barrier: threading.Barrier,
    connect_timeout_seconds: float,
    read_timeout_seconds: float,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []

    with requests.Session() as session:
        barrier.wait()

        for sequence_number in range(
            1,
            requests_per_worker + 1,
        ):
            request_number = (
                (worker_number - 1) * requests_per_worker
                + sequence_number
            )

            request_id = (
                f"{run_id}-"
                f"worker{worker_number:02d}-"
                f"request{sequence_number:03d}"
            )

            started_at = utc_timestamp()
            started = time.perf_counter()

            base_row: dict[str, Any] = {
                "run_id": run_id,
                "strategy": strategy,
                "worker_number": worker_number,
                "sequence_number": sequence_number,
                "request_number": request_number,
                "request_id": request_id,
                "client_started_at_utc": started_at,
            }

            try:
                response = session.get(
                    TIMING_ENDPOINT,
                    headers={"X-Request-ID": request_id},
                    timeout=(
                        connect_timeout_seconds,
                        read_timeout_seconds,
                    ),
                )

                client_elapsed_ms = (
                    time.perf_counter() - started
                ) * 1000

                response.raise_for_status()
                payload = response.json()

                actual_strategy = payload[
                    "connection_strategy"
                ]

                if actual_strategy != strategy:
                    raise RuntimeError(
                        "Response strategy mismatch: "
                        f"expected {strategy!r}, "
                        f"received {actual_strategy!r}"
                    )

                phases = payload["database_phases"]

                missing_phases = [
                    phase_name
                    for phase_name in DATABASE_PHASE_NAMES
                    if phase_name not in phases
                ]

                if missing_phases:
                    raise RuntimeError(
                        "Response is missing database phases: "
                        + ", ".join(missing_phases)
                    )

                resources = payload["database_resources"]
                pool = resources.get("pool")

                if strategy == "bounded_pool" and pool is None:
                    raise RuntimeError(
                        "Bounded-pool response contains no pool state"
                    )

                if (
                    strategy == "connection_per_operation"
                    and pool is not None
                ):
                    raise RuntimeError(
                        "Direct strategy unexpectedly returned "
                        "pool state"
                    )

                statistics = (
                    pool.get("statistics", {})
                    if pool is not None
                    else {}
                )

                rows.append(
                    {
                        **base_row,
                        "client_finished_at_utc": utc_timestamp(),
                        "client_elapsed_ms": round(
                            client_elapsed_ms,
                            3,
                        ),
                        "status_code": response.status_code,
                        "response_request_id": (
                            response.headers.get(
                                "X-Request-ID",
                                "",
                            )
                        ),
                        "outcome": "success",
                        "error_type": "",
                        "error_message": "",
                        "acquire_ms": phases["acquire_ms"],
                        "query_ms": phases["query_ms"],
                        "fetch_ms": phases["fetch_ms"],
                        "release_ms": phases["release_ms"],
                        "database_total_ms": phases["total_ms"],
                        "pool_size": statistics.get(
                            "pool_size",
                            "",
                        ),
                        "pool_available": statistics.get(
                            "pool_available",
                            "",
                        ),
                        "requests_waiting": statistics.get(
                            "requests_waiting",
                            "",
                        ),
                        "requests_queued": statistics.get(
                            "requests_queued",
                            "",
                        ),
                    }
                )

            except Exception as exc:
                client_elapsed_ms = (
                    time.perf_counter() - started
                ) * 1000

                rows.append(
                    {
                        **base_row,
                        "client_finished_at_utc": utc_timestamp(),
                        "client_elapsed_ms": round(
                            client_elapsed_ms,
                            3,
                        ),
                        "status_code": "",
                        "response_request_id": "",
                        "outcome": "failure",
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                        "acquire_ms": "",
                        "query_ms": "",
                        "fetch_ms": "",
                        "release_ms": "",
                        "database_total_ms": "",
                        "pool_size": "",
                        "pool_available": "",
                        "requests_waiting": "",
                        "requests_queued": "",
                    }
                )

    return rows


def capture_api_logs(
    *,
    run_id: str,
    output_path: Path,
) -> int:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "logs",
            "--since",
            "10m",
            "api",
        ],
        cwd=REPOSITORY_ROOT,
        check=False,
        capture_output=True,
        text=True,
    )

    matching_lines = [
        line
        for line in result.stdout.splitlines()
        if run_id in line
    ]

    output_path.write_text(
        "\n".join(matching_lines) + (
            "\n" if matching_lines else ""
        ),
        encoding="utf-8",
    )

    return len(matching_lines)


def build_summary(
    *,
    rows: list[dict[str, Any]],
    run_id: str,
    strategy: str,
    mode: str,
    request_count: int,
    concurrency: int,
    elapsed_seconds: float,
    starting_state_run_id: str,
    api_log_line_count: int,
) -> dict[str, Any]:
    successful_rows = [
        row
        for row in rows
        if row["outcome"] == "success"
    ]

    failed_rows = [
        row
        for row in rows
        if row["outcome"] != "success"
    ]

    metrics: dict[str, Any] = {
        "client_elapsed_ms": metric_summary(
            [
                float(row["client_elapsed_ms"])
                for row in successful_rows
            ]
        )
    }

    for phase_name in DATABASE_PHASE_NAMES:
        source_name = (
            "database_total_ms"
            if phase_name == "total_ms"
            else phase_name
        )

        metrics[phase_name] = metric_summary(
            [
                float(row[source_name])
                for row in successful_rows
            ]
        )

    pool_rows = [
        row
        for row in successful_rows
        if row["pool_size"] != ""
    ]

    pool_observations: dict[str, Any] | None = None

    if pool_rows:
        pool_observations = {
            "maximum_pool_size": max(
                int(row["pool_size"])
                for row in pool_rows
            ),
            "minimum_available": min(
                int(row["pool_available"])
                for row in pool_rows
            ),
            "maximum_requests_waiting": max(
                int(row["requests_waiting"])
                for row in pool_rows
            ),
            "highest_cumulative_requests_queued_since_api_start": max(
                int(row["requests_queued"] or 0)
                for row in pool_rows
            ),
        }

    return {
        "run_id": run_id,
        "strategy": strategy,
        "mode": mode,
        "starting_state_run_id": starting_state_run_id,
        "request_count": request_count,
        "concurrency": concurrency,
        "requests_per_worker": (
            request_count // concurrency
        ),
        "success_count": len(successful_rows),
        "failure_count": len(failed_rows),
        "failure_rate_percent": round(
            100 * len(failed_rows) / request_count,
            3,
        ),
        "elapsed_seconds": round(elapsed_seconds, 3),
        "requests_per_second": round(
            request_count / elapsed_seconds,
            3,
        ),
        "metrics": metrics,
        "pool_observations": pool_observations,
        "api_log_line_count": api_log_line_count,
        "failures": [
            {
                "request_id": row["request_id"],
                "error_type": row["error_type"],
                "error_message": row["error_message"],
            }
            for row in failed_rows[:20]
        ],
    }


def write_markdown_report(
    summary: dict[str, Any],
    output_path: Path,
) -> None:
    metrics = summary["metrics"]

    lines = [
        "# Database Connection Study Run",
        "",
        f"- Run ID: `{summary['run_id']}`",
        f"- Strategy: `{summary['strategy']}`",
        f"- Mode: `{summary['mode']}`",
        (
            "- Starting-state run: "
            f"`{summary['starting_state_run_id']}`"
        ),
        f"- Requests: {summary['request_count']}",
        f"- Concurrency: {summary['concurrency']}",
        f"- Successes: {summary['success_count']}",
        f"- Failures: {summary['failure_count']}",
        (
            "- Throughput: "
            f"{summary['requests_per_second']} requests/second"
        ),
        "",
        "## Timing Summary",
        "",
        "| Metric | Mean | p50 | p95 | p99 | Maximum |",
        "|---|---:|---:|---:|---:|---:|",
    ]

    display_names = {
        "client_elapsed_ms": "Client elapsed",
        "acquire_ms": "Database acquire",
        "query_ms": "Query execution",
        "fetch_ms": "Fetch",
        "release_ms": "Database release",
        "total_ms": "Database total",
    }

    for metric_name, display_name in display_names.items():
        values = metrics[metric_name]

        lines.append(
            "| "
            f"{display_name} | "
            f"{values['mean_ms']} | "
            f"{values['p50_ms']} | "
            f"{values['p95_ms']} | "
            f"{values['p99_ms']} | "
            f"{values['maximum_ms']} |"
        )

    if summary["pool_observations"] is not None:
        pool = summary["pool_observations"]

        lines.extend(
            [
                "",
                "## Pool Observations",
                "",
                (
                    "- Maximum pool size observed: "
                    f"{pool['maximum_pool_size']}"
                ),
                (
                    "- Minimum available connections: "
                    f"{pool['minimum_available']}"
                ),
                (
                    "- Maximum requests waiting: "
                    f"{pool['maximum_requests_waiting']}"
                ),
                (
                    "- Highest cumulative requests queued since API start: "
                    f"{pool['highest_cumulative_requests_queued_since_api_start']}"
                ),
            ]
        )

    output_path.write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--expected-strategy",
        required=True,
        choices=sorted(SUPPORTED_STRATEGIES),
    )

    parser.add_argument(
        "--mode",
        choices=["warm", "cold"],
        default="warm",
    )

    parser.add_argument(
        "--request-count",
        type=int,
        default=200,
    )

    parser.add_argument(
        "--concurrency",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--warmup-count",
        type=int,
        default=20,
    )

    parser.add_argument(
        "--stabilization-seconds",
        type=float,
        default=2.0,
    )

    parser.add_argument(
        "--connect-timeout-seconds",
        type=float,
        default=3.0,
    )

    parser.add_argument(
        "--read-timeout-seconds",
        type=float,
        default=10.0,
    )

    arguments = parser.parse_args()

    if arguments.request_count <= 0:
        raise ValueError(
            "--request-count must be greater than zero"
        )

    if arguments.concurrency <= 0:
        raise ValueError(
            "--concurrency must be greater than zero"
        )

    if (
        arguments.request_count
        % arguments.concurrency
        != 0
    ):
        raise ValueError(
            "--request-count must be divisible by "
            "--concurrency"
        )

    if arguments.mode == "cold":
        arguments.warmup_count = 0

    TEST_RUNS_DIRECTORY.mkdir(
        parents=True,
        exist_ok=True,
    )

    (
        starting_state_run_id,
        starting_state_manifest_path,
        starting_state_manifest,
    ) = run_starting_state_preparation(
        mode=arguments.mode,
        warmup_count=arguments.warmup_count,
        stabilization_seconds=(
            arguments.stabilization_seconds
        ),
    )

    validate_starting_state(
        starting_state_manifest,
        arguments.expected_strategy,
    )

    run_id = utc_now().strftime(
        "database-connection-"
        f"{arguments.expected_strategy}-"
        f"{arguments.mode}-"
        "%Y%m%dT%H%M%S%fZ"
    )

    run_directory = TEST_RUNS_DIRECTORY / run_id
    run_directory.mkdir(parents=True, exist_ok=False)

    shutil.copy2(
        starting_state_manifest_path,
        run_directory / "starting-state.json",
    )

    barrier = threading.Barrier(
        arguments.concurrency
    )

    requests_per_worker = (
        arguments.request_count
        // arguments.concurrency
    )

    started = time.perf_counter()
    rows: list[dict[str, Any]] = []

    with ThreadPoolExecutor(
        max_workers=arguments.concurrency
    ) as executor:
        futures = [
            executor.submit(
                execute_worker,
                worker_number=worker_number,
                requests_per_worker=requests_per_worker,
                strategy=arguments.expected_strategy,
                run_id=run_id,
                barrier=barrier,
                connect_timeout_seconds=(
                    arguments.connect_timeout_seconds
                ),
                read_timeout_seconds=(
                    arguments.read_timeout_seconds
                ),
            )
            for worker_number in range(
                1,
                arguments.concurrency + 1,
            )
        ]

        for future in as_completed(futures):
            rows.extend(future.result())

    elapsed_seconds = time.perf_counter() - started

    rows.sort(
        key=lambda row: int(row["request_number"])
    )

    client_csv_path = run_directory / "client-results.csv"

    with client_csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)

    time.sleep(2)

    api_log_line_count = capture_api_logs(
        run_id=run_id,
        output_path=run_directory / "api.log",
    )

    summary = build_summary(
        rows=rows,
        run_id=run_id,
        strategy=arguments.expected_strategy,
        mode=arguments.mode,
        request_count=arguments.request_count,
        concurrency=arguments.concurrency,
        elapsed_seconds=elapsed_seconds,
        starting_state_run_id=starting_state_run_id,
        api_log_line_count=api_log_line_count,
    )

    summary_path = run_directory / "summary.json"
    summary_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    write_markdown_report(
        summary,
        run_directory / "report.md",
    )

    (
        TEST_RUNS_DIRECTORY
        / "latest-database-connection-run.txt"
    ).write_text(
        run_id,
        encoding="utf-8",
    )

    print()
    print("DATABASE CONNECTION STUDY RUN")
    print("-----------------------------")
    print(json.dumps(summary, indent=2))
    print()
    print("Evidence directory:", run_directory)

    if summary["failure_count"] != 0:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
