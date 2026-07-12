from __future__ import annotations

import argparse
import csv
import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import requests


BASE_URL = "http://localhost:8000"
TARGET_URL = f"{BASE_URL}/patients/1001"
HEALTH_URL = f"{BASE_URL}/health"

REQUEST_COUNT = 200
CONCURRENCY = 20
REQUESTS_PER_WORKER = REQUEST_COUNT // CONCURRENCY

CONNECT_TIMEOUT_SECONDS = 3
READ_TIMEOUT_SECONDS = 10

REPORTS_DIRECTORY = Path("reports")
REPORTS_DIRECTORY.mkdir(parents=True, exist_ok=True)


def utc_timestamp() -> str:
    return datetime.now(UTC).isoformat()


def percentile(values: list[float], percent: int) -> float | None:
    if not values:
        return None

    ordered = sorted(values)
    rank = math.ceil((percent / 100) * len(ordered))
    index = max(0, min(len(ordered) - 1, rank - 1))
    return ordered[index]


def latency_summary(values: list[float]) -> dict[str, Any]:
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
        "p50_ms": round(percentile(values, 50) or 0, 3),
        "p95_ms": round(percentile(values, 95) or 0, 3),
        "p99_ms": round(percentile(values, 99) or 0, 3),
        "maximum_ms": round(max(values), 3),
    }


parser = argparse.ArgumentParser()
parser.add_argument(
    "--mode",
    required=True,
    choices=["fresh", "keepalive"],
)
arguments = parser.parse_args()

mode = arguments.mode

run_id = datetime.now(UTC).strftime(
    f"http-{mode}-%Y%m%dT%H%M%S%fZ"
)

csv_path = REPORTS_DIRECTORY / f"{run_id}-client.csv"
summary_path = REPORTS_DIRECTORY / f"{run_id}-client-summary.json"
latest_run_path = REPORTS_DIRECTORY / "latest_correlated_run_id.txt"

start_barrier = threading.Barrier(CONCURRENCY)

# Equal global readiness check before either measured mode.
health_response = requests.get(
    HEALTH_URL,
    timeout=(CONNECT_TIMEOUT_SECONDS, READ_TIMEOUT_SECONDS),
)
health_response.raise_for_status()


def execute_request(
    request_client: requests.Session | None,
    request_id: str,
) -> requests.Response:
    if request_client is None:
        return requests.get(
            TARGET_URL,
            headers={"X-Request-ID": request_id},
            timeout=(
                CONNECT_TIMEOUT_SECONDS,
                READ_TIMEOUT_SECONDS,
            ),
        )

    return request_client.get(
        TARGET_URL,
        headers={"X-Request-ID": request_id},
        timeout=(
            CONNECT_TIMEOUT_SECONDS,
            READ_TIMEOUT_SECONDS,
        ),
    )


def run_worker(worker_number: int) -> list[dict[str, Any]]:
    results: list[dict[str, Any]] = []

    session = requests.Session() if mode == "keepalive" else None

    try:
        start_barrier.wait()

        for sequence_number in range(1, REQUESTS_PER_WORKER + 1):
            request_number = (
                (worker_number - 1) * REQUESTS_PER_WORKER
                + sequence_number
            )

            request_id = (
                f"{run_id}-"
                f"worker{worker_number:02d}-"
                f"request{sequence_number:02d}"
            )

            client_started_at = utc_timestamp()
            started = time.perf_counter()

            try:
                response = execute_request(session, request_id)
                elapsed_ms = (time.perf_counter() - started) * 1000

                result = {
                    "run_id": run_id,
                    "mode": mode,
                    "worker_number": worker_number,
                    "sequence_number": sequence_number,
                    "request_number": request_number,
                    "request_id": request_id,
                    "client_started_at_utc": client_started_at,
                    "client_finished_at_utc": utc_timestamp(),
                    "client_elapsed_ms": round(elapsed_ms, 3),
                    "status_code": response.status_code,
                    "response_request_id": response.headers.get(
                        "X-Request-ID",
                        "",
                    ),
                    "outcome": "success",
                    "error_type": "",
                    "error_message": "",
                }

            except requests.ConnectTimeout as exc:
                outcome = "connect_timeout"
                error_type = type(exc).__name__
                error_message = str(exc)

            except requests.ReadTimeout as exc:
                outcome = "read_timeout"
                error_type = type(exc).__name__
                error_message = str(exc)

            except requests.RequestException as exc:
                outcome = "request_error"
                error_type = type(exc).__name__
                error_message = str(exc)

            else:
                results.append(result)
                continue

            elapsed_ms = (time.perf_counter() - started) * 1000

            results.append(
                {
                    "run_id": run_id,
                    "mode": mode,
                    "worker_number": worker_number,
                    "sequence_number": sequence_number,
                    "request_number": request_number,
                    "request_id": request_id,
                    "client_started_at_utc": client_started_at,
                    "client_finished_at_utc": utc_timestamp(),
                    "client_elapsed_ms": round(elapsed_ms, 3),
                    "status_code": "",
                    "response_request_id": "",
                    "outcome": outcome,
                    "error_type": error_type,
                    "error_message": error_message,
                }
            )

    finally:
        if session is not None:
            session.close()

    return results


test_started_at = utc_timestamp()
test_started = time.perf_counter()

all_results: list[dict[str, Any]] = []

with ThreadPoolExecutor(max_workers=CONCURRENCY) as executor:
    futures = [
        executor.submit(run_worker, worker_number)
        for worker_number in range(1, CONCURRENCY + 1)
    ]

    for future in as_completed(futures):
        all_results.extend(future.result())

test_elapsed_seconds = time.perf_counter() - test_started
test_finished_at = utc_timestamp()

all_results.sort(key=lambda row: int(row["request_number"]))

with csv_path.open("w", newline="", encoding="utf-8") as csv_file:
    writer = csv.DictWriter(
        csv_file,
        fieldnames=list(all_results[0].keys()),
    )
    writer.writeheader()
    writer.writerows(all_results)

all_latencies = [
    float(result["client_elapsed_ms"])
    for result in all_results
]

successful_latencies = [
    float(result["client_elapsed_ms"])
    for result in all_results
    if result["outcome"] == "success"
]

outcome_counts: dict[str, int] = {}

for result in all_results:
    outcome = str(result["outcome"])
    outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1

summary = {
    "run_id": run_id,
    "mode": mode,
    "request_count": REQUEST_COUNT,
    "concurrency": CONCURRENCY,
    "requests_per_worker": REQUESTS_PER_WORKER,
    "connect_timeout_seconds": CONNECT_TIMEOUT_SECONDS,
    "read_timeout_seconds": READ_TIMEOUT_SECONDS,
    "test_started_at_utc": test_started_at,
    "test_finished_at_utc": test_finished_at,
    "test_elapsed_seconds": round(test_elapsed_seconds, 3),
    "requests_per_second": round(
        REQUEST_COUNT / test_elapsed_seconds,
        3,
    ),
    "outcomes": outcome_counts,
    "all_requests": latency_summary(all_latencies),
    "successful_requests": latency_summary(successful_latencies),
}

summary_path.write_text(
    json.dumps(summary, indent=2),
    encoding="utf-8",
)

latest_run_path.write_text(run_id, encoding="utf-8")

print()
print(f"CONTROLLED HTTP MODE: {mode.upper()}")
print("--------------------------------")
print(json.dumps(summary, indent=2))
print()
print("Client CSV:", csv_path)
print("Client summary:", summary_path)
print("Run ID:", run_id)
print()
print("Waiting 12 seconds for queued server work...")
time.sleep(12)
