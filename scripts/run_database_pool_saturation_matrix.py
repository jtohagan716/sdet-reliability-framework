from __future__ import annotations

import argparse
import csv
import json
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import requests


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
STUDY_SCRIPT = (
    REPOSITORY_ROOT
    / "scripts"
    / "run_database_connection_study.py"
)
TEST_RUNS_DIRECTORY = (
    REPOSITORY_ROOT
    / "reports"
    / "test-runs"
)

TIMING_ENDPOINT = (
    "http://localhost:8000/"
    "qa/database-connection-timing?patient_id=1001"
)

DEFAULT_CONCURRENCIES = [4, 8, 12, 20, 40]


def utc_run_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime(
        "%Y%m%dT%H%M%S%fZ"
    )
    return f"database-pool-saturation-matrix-{timestamp}"


def run_command(
    command: list[str],
    *,
    capture_output: bool = False,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture_output,
        check=True,
    )


def restart_api() -> None:
    print("\nRestarting API to reset pool statistics...")

    run_command(
        [
            "docker",
            "compose",
            "restart",
            "api",
        ]
    )


def wait_for_api(timeout_seconds: float) -> None:
    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None

    while time.monotonic() < deadline:
        try:
            response = requests.get(
                TIMING_ENDPOINT,
                timeout=(3, 10),
            )

            response.raise_for_status()

            payload = response.json()

            if payload.get("connection_strategy") != "bounded_pool":
                raise RuntimeError(
                    "API is not using the bounded_pool strategy"
                )

            print("API is ready.")
            return

        except Exception as exc:
            last_error = exc
            time.sleep(1)

    raise RuntimeError(
        "API did not become ready within "
        f"{timeout_seconds} seconds: {last_error}"
    )


def run_study(
    *,
    concurrency: int,
    repetition: int,
    request_count: int,
    warmup_count: int,
    stabilization_seconds: float,
    connect_timeout_seconds: float,
    read_timeout_seconds: float,
) -> tuple[dict[str, Any], Path]:
    configuration_label = (
        f"saturation-c{concurrency:02d}-r{repetition:02d}"
    )

    command = [
        sys.executable,
        str(STUDY_SCRIPT),
        "--expected-strategy",
        "bounded_pool",
        "--configuration-label",
        configuration_label,
        "--mode",
        "warm",
        "--request-count",
        str(request_count),
        "--concurrency",
        str(concurrency),
        "--warmup-count",
        str(warmup_count),
        "--stabilization-seconds",
        str(stabilization_seconds),
        "--connect-timeout-seconds",
        str(connect_timeout_seconds),
        "--read-timeout-seconds",
        str(read_timeout_seconds),
    ]

    print(
        "\nRunning matrix point: "
        f"concurrency={concurrency}, "
        f"repetition={repetition}"
    )

    completed = subprocess.run(
        command,
        cwd=REPOSITORY_ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    print(completed.stdout, end="")

    if completed.returncode != 0:
        raise RuntimeError(
            "Database connection study failed for "
            f"concurrency={concurrency}, "
            f"repetition={repetition}"
        )

    evidence_prefix = "Evidence directory:"

    evidence_lines = [
        line
        for line in completed.stdout.splitlines()
        if line.startswith(evidence_prefix)
    ]

    if len(evidence_lines) != 1:
        raise RuntimeError(
            "Unable to determine the study evidence directory"
        )

    evidence_directory = Path(
        evidence_lines[0]
        .removeprefix(evidence_prefix)
        .strip()
    )

    summary_path = evidence_directory / "summary.json"

    if not summary_path.exists():
        raise RuntimeError(
            f"Study summary does not exist: {summary_path}"
        )

    summary = json.loads(
        summary_path.read_text(encoding="utf-8")
    )

    return summary, evidence_directory


def count_idle_in_transaction() -> int:
    sql = (
        "SELECT COUNT(*) "
        "FROM pg_stat_activity "
        "WHERE datname = 'sdet_reliability' "
        "AND state = 'idle in transaction';"
    )

    completed = run_command(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "sdet_user",
            "-d",
            "sdet_reliability",
            "-Atc",
            sql,
        ],
        capture_output=True,
    )

    output_lines = [
        line.strip()
        for line in completed.stdout.splitlines()
        if line.strip()
    ]

    if not output_lines:
        raise RuntimeError(
            "PostgreSQL returned no idle-in-transaction count"
        )

    return int(output_lines[-1])


def collect_recovery_state(
    recovery_seconds: float,
) -> dict[str, Any]:
    print(
        f"Allowing {recovery_seconds} seconds for recovery..."
    )

    time.sleep(recovery_seconds)

    response = requests.get(
        TIMING_ENDPOINT,
        timeout=(3, 15),
    )
    response.raise_for_status()

    payload = response.json()
    pool = payload["database_resources"]["pool"]
    statistics = pool["statistics"]

    pool_size = int(statistics["pool_size"])
    pool_available = int(statistics["pool_available"])
    requests_waiting = int(
        statistics["requests_waiting"]
    )
    idle_in_transaction = count_idle_in_transaction()

    recovered = (
        pool_available == pool_size
        and requests_waiting == 0
        and idle_in_transaction == 0
    )

    recovery = {
        "pool_size": pool_size,
        "pool_available": pool_available,
        "requests_waiting": requests_waiting,
        "idle_in_transaction": idle_in_transaction,
        "recovered": recovered,
    }

    print(
        "Recovery state: "
        f"available={pool_available}/{pool_size}, "
        f"waiting={requests_waiting}, "
        f"idle_in_transaction={idle_in_transaction}, "
        f"recovered={recovered}"
    )

    return recovery


def flatten_result(
    *,
    summary: dict[str, Any],
    evidence_directory: Path,
    repetition: int,
    recovery: dict[str, Any],
) -> dict[str, Any]:
    metrics = summary["metrics"]
    pool = summary["pool_observations"] or {}

    return {
        "run_id": summary["run_id"],
        "concurrency": summary["concurrency"],
        "repetition": repetition,
        "request_count": summary["request_count"],
        "success_count": summary["success_count"],
        "failure_count": summary["failure_count"],
        "requests_per_second": summary[
            "requests_per_second"
        ],
        "client_p50_ms": metrics[
            "client_elapsed_ms"
        ]["p50_ms"],
        "client_p95_ms": metrics[
            "client_elapsed_ms"
        ]["p95_ms"],
        "client_p99_ms": metrics[
            "client_elapsed_ms"
        ]["p99_ms"],
        "acquire_p50_ms": metrics["acquire_ms"]["p50_ms"],
        "acquire_p95_ms": metrics["acquire_ms"]["p95_ms"],
        "acquire_p99_ms": metrics["acquire_ms"]["p99_ms"],
        "database_total_p95_ms": metrics[
            "total_ms"
        ]["p95_ms"],
        "maximum_pool_size": pool.get(
            "maximum_pool_size"
        ),
        "minimum_available": pool.get(
            "minimum_available"
        ),
        "maximum_requests_waiting": pool.get(
            "maximum_requests_waiting"
        ),
        "cumulative_requests_queued": pool.get(
            "highest_cumulative_requests_queued_since_api_start"
        ),
        "recovery_pool_size": recovery["pool_size"],
        "recovery_pool_available": recovery[
            "pool_available"
        ],
        "recovery_requests_waiting": recovery[
            "requests_waiting"
        ],
        "recovery_idle_in_transaction": recovery[
            "idle_in_transaction"
        ],
        "recovered": recovery["recovered"],
        "evidence_directory": str(evidence_directory),
    }


def median_for(
    rows: list[dict[str, Any]],
    field_name: str,
) -> float:
    return round(
        statistics.median(
            float(row[field_name])
            for row in rows
        ),
        3,
    )


def build_concurrency_summaries(
    rows: list[dict[str, Any]],
    concurrencies: list[int],
) -> list[dict[str, Any]]:
    summaries: list[dict[str, Any]] = []

    for concurrency in concurrencies:
        matching_rows = [
            row
            for row in rows
            if int(row["concurrency"]) == concurrency
        ]

        summaries.append(
            {
                "concurrency": concurrency,
                "repetitions": len(matching_rows),
                "median_requests_per_second": median_for(
                    matching_rows,
                    "requests_per_second",
                ),
                "median_client_p95_ms": median_for(
                    matching_rows,
                    "client_p95_ms",
                ),
                "median_client_p99_ms": median_for(
                    matching_rows,
                    "client_p99_ms",
                ),
                "median_acquire_p95_ms": median_for(
                    matching_rows,
                    "acquire_p95_ms",
                ),
                "median_acquire_p99_ms": median_for(
                    matching_rows,
                    "acquire_p99_ms",
                ),
                "median_database_total_p95_ms": median_for(
                    matching_rows,
                    "database_total_p95_ms",
                ),
                "maximum_requests_waiting": max(
                    int(row["maximum_requests_waiting"])
                    for row in matching_rows
                ),
                "total_failures": sum(
                    int(row["failure_count"])
                    for row in matching_rows
                ),
                "all_runs_recovered": all(
                    bool(row["recovered"])
                    for row in matching_rows
                ),
            }
        )

    return summaries


def write_csv(
    rows: list[dict[str, Any]],
    path: Path,
) -> None:
    with path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=list(rows[0].keys()),
        )
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_report(
    *,
    matrix_run_id: str,
    summaries: list[dict[str, Any]],
    path: Path,
) -> None:
    lines = [
        "# Database Connection Pool Saturation Matrix",
        "",
        f"Matrix run ID: `{matrix_run_id}`",
        "",
        "| Concurrency | Median RPS | Client p95 ms | "
        "Acquire p95 ms | DB total p95 ms | "
        "Max waiting | Failures | Recovered |",
        "|---:|---:|---:|---:|---:|---:|---:|:---:|",
    ]

    for summary in summaries:
        lines.append(
            "| "
            f"{summary['concurrency']} | "
            f"{summary['median_requests_per_second']} | "
            f"{summary['median_client_p95_ms']} | "
            f"{summary['median_acquire_p95_ms']} | "
            f"{summary['median_database_total_p95_ms']} | "
            f"{summary['maximum_requests_waiting']} | "
            f"{summary['total_failures']} | "
            f"{summary['all_runs_recovered']} |"
        )

    lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            "- Use medians across repetitions rather than a single run.",
            "- Treat rising acquisition latency and waiting requests "
            "as evidence of pool contention.",
            "- Confirm the physical pool remains bounded at its "
            "configured maximum.",
            "- Require complete post-run recovery and zero "
            "idle-in-transaction sessions.",
            "",
        ]
    )

    path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a repeated PostgreSQL connection-pool "
            "saturation matrix."
        )
    )

    parser.add_argument(
        "--concurrencies",
        type=int,
        nargs="+",
        default=DEFAULT_CONCURRENCIES,
    )
    parser.add_argument(
        "--repetitions",
        type=int,
        default=3,
    )
    parser.add_argument(
        "--request-count",
        type=int,
        default=240,
    )
    parser.add_argument(
        "--warmup-count",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--stabilization-seconds",
        type=float,
        default=2,
    )
    parser.add_argument(
        "--recovery-seconds",
        type=float,
        default=5,
    )
    parser.add_argument(
        "--connect-timeout-seconds",
        type=float,
        default=3,
    )
    parser.add_argument(
        "--read-timeout-seconds",
        type=float,
        default=15,
    )
    parser.add_argument(
        "--api-ready-timeout-seconds",
        type=float,
        default=60,
    )

    return parser.parse_args()


def main() -> int:
    args = parse_arguments()

    for concurrency in args.concurrencies:
        if args.request_count % concurrency != 0:
            raise ValueError(
                f"Request count {args.request_count} "
                f"is not divisible by concurrency "
                f"{concurrency}"
            )

    matrix_run_id = utc_run_id()
    output_directory = (
        TEST_RUNS_DIRECTORY / matrix_run_id
    )
    output_directory.mkdir(
        parents=True,
        exist_ok=False,
    )

    rows: list[dict[str, Any]] = []

    print("DATABASE POOL SATURATION MATRIX")
    print("--------------------------------")
    print(f"Matrix run ID: {matrix_run_id}")
    print(f"Concurrencies: {args.concurrencies}")
    print(f"Repetitions: {args.repetitions}")
    print(f"Request count per run: {args.request_count}")

    for concurrency in args.concurrencies:
        for repetition in range(
            1,
            args.repetitions + 1,
        ):
            restart_api()
            wait_for_api(
                args.api_ready_timeout_seconds
            )

            summary, evidence_directory = run_study(
                concurrency=concurrency,
                repetition=repetition,
                request_count=args.request_count,
                warmup_count=args.warmup_count,
                stabilization_seconds=(
                    args.stabilization_seconds
                ),
                connect_timeout_seconds=(
                    args.connect_timeout_seconds
                ),
                read_timeout_seconds=(
                    args.read_timeout_seconds
                ),
            )

            recovery = collect_recovery_state(
                args.recovery_seconds
            )

            rows.append(
                flatten_result(
                    summary=summary,
                    evidence_directory=evidence_directory,
                    repetition=repetition,
                    recovery=recovery,
                )
            )

    summaries = build_concurrency_summaries(
        rows,
        args.concurrencies,
    )

    write_csv(
        rows,
        output_directory / "matrix-results.csv",
    )

    matrix_summary = {
        "matrix_run_id": matrix_run_id,
        "configuration": {
            "concurrencies": args.concurrencies,
            "repetitions": args.repetitions,
            "request_count_per_run": args.request_count,
            "warmup_count": args.warmup_count,
            "stabilization_seconds": (
                args.stabilization_seconds
            ),
            "recovery_seconds": args.recovery_seconds,
            "connect_timeout_seconds": (
                args.connect_timeout_seconds
            ),
            "read_timeout_seconds": (
                args.read_timeout_seconds
            ),
        },
        "concurrency_summaries": summaries,
        "runs": rows,
    }

    (
        output_directory / "matrix-summary.json"
    ).write_text(
        json.dumps(
            matrix_summary,
            indent=2,
        ),
        encoding="utf-8",
    )

    write_markdown_report(
        matrix_run_id=matrix_run_id,
        summaries=summaries,
        path=output_directory / "report.md",
    )

    all_recovered = all(
        bool(row["recovered"])
        for row in rows
    )
    total_failures = sum(
        int(row["failure_count"])
        for row in rows
    )

    print("\nDATABASE POOL SATURATION MATRIX COMPLETE")
    print("----------------------------------------")
    print(f"Runs completed: {len(rows)}")
    print(f"Total request failures: {total_failures}")
    print(f"All runs recovered: {all_recovered}")
    print(f"Evidence directory: {output_directory}")

    return 0 if all_recovered else 1


if __name__ == "__main__":
    raise SystemExit(main())