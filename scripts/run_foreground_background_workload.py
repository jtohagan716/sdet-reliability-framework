from __future__ import annotations

import argparse
import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

import requests

try:
    from scripts.encounter_workload_data import (
        EncounterWorkloadDataset,
        build_workload_dataset,
        prepare_workload_dataset,
        remove_workload_dataset,
    )
except ModuleNotFoundError:
    from encounter_workload_data import (
        EncounterWorkloadDataset,
        build_workload_dataset,
        prepare_workload_dataset,
        remove_workload_dataset,
    )


DEFAULT_API_BASE_URL = "http://localhost:8000"
EXPECTED_CONNECTION_STRATEGY = "bounded_pool"

DATABASE_PHASE_NAMES = (
    "acquire_ms",
    "query_ms",
    "fetch_ms",
    "release_ms",
    "total_ms",
)


@dataclass(frozen=True)
class WorkloadConfiguration:
    """Describe one workload executed during the mixed study."""

    request_count: int
    concurrency: int

    @property
    def requests_per_worker(self) -> int:
        """Return the number of requests executed by each worker."""

        return self.request_count // self.concurrency

    def validate(self, workload_name: str) -> None:
        """Reject invalid or nondeterministic worker configurations."""

        if self.request_count <= 0:
            raise ValueError(
                f"{workload_name} request count must be greater than zero"
            )

        if self.concurrency <= 0:
            raise ValueError(
                f"{workload_name} concurrency must be greater than zero"
            )

        if self.request_count % self.concurrency != 0:
            raise ValueError(
                f"{workload_name} request count must be divisible by "
                f"{workload_name} concurrency"
            )


@dataclass(frozen=True)
class MixedWorkloadConfiguration:
    """Describe one foreground-versus-background experiment."""

    foreground: WorkloadConfiguration
    background: WorkloadConfiguration
    foreground_connection_hold_ms: int
    background_batch_size: int
    connect_timeout_seconds: float
    read_timeout_seconds: float

    @property
    def required_encounter_count(self) -> int:
        """Return the scheduled encounters required by the run."""

        return (
            self.background.request_count
            * self.background_batch_size
        )

    @property
    def total_concurrency(self) -> int:
        """Return the combined number of concurrent workers."""

        return (
            self.foreground.concurrency
            + self.background.concurrency
        )

    def validate(self) -> None:
        """Validate every setting before changing database state."""

        self.foreground.validate("foreground")
        self.background.validate("background")

        if not 0 <= self.foreground_connection_hold_ms <= 1000:
            raise ValueError(
                "foreground connection hold must be between "
                "0 and 1000 milliseconds"
            )

        if not 1 <= self.background_batch_size <= 100:
            raise ValueError(
                "background batch size must be between 1 and 100"
            )

        if self.connect_timeout_seconds <= 0:
            raise ValueError(
                "connect timeout must be greater than zero"
            )

        if self.read_timeout_seconds <= 0:
            raise ValueError(
                "read timeout must be greater than zero"
            )


def utc_now() -> datetime:
    """Return the current timezone-aware UTC datetime."""

    return datetime.now(UTC)


def utc_timestamp() -> str:
    """Return an ISO-formatted UTC timestamp."""

    return utc_now().isoformat()


def get_api_base_url() -> str:
    """Return the configured FastAPI base URL."""

    return os.getenv(
        "SDET_API_BASE_URL",
        DEFAULT_API_BASE_URL,
    ).rstrip("/")


def percentile(
    values: list[float],
    percent: int,
) -> float | None:
    """Return a nearest-rank percentile rounded to three decimals."""

    if not values:
        return None

    ordered = sorted(values)
    rank = math.ceil((percent / 100) * len(ordered))
    index = max(0, min(len(ordered) - 1, rank - 1))

    return round(ordered[index], 3)


def metric_summary(
    values: list[float],
) -> dict[str, float | int | None]:
    """Build a repeatable latency summary for one metric."""

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


def extract_database_timings(
    payload: dict[str, Any],
    *,
    field_name: str,
) -> dict[str, float]:
    """Validate and return the database timing measurements."""

    phases = payload.get(field_name)

    if not isinstance(phases, dict):
        raise RuntimeError(
            f"Response contains no {field_name!r} object"
        )

    missing_phases = [
        phase_name
        for phase_name in DATABASE_PHASE_NAMES
        if phase_name not in phases
    ]

    if missing_phases:
        raise RuntimeError(
            "Response is missing database timing phases: "
            + ", ".join(missing_phases)
        )

    normalized: dict[str, float] = {}

    for phase_name in DATABASE_PHASE_NAMES:
        value = float(phases[phase_name])

        if value < 0:
            raise RuntimeError(
                f"Database timing {phase_name!r} cannot be negative"
            )

        normalized[phase_name] = value

    return normalized


def extract_pool_statistics(
    payload: dict[str, Any],
) -> dict[str, int]:
    """Validate and return the bounded-pool statistics."""

    resources = payload.get("database_resources")

    if not isinstance(resources, dict):
        raise RuntimeError(
            "Response contains no database_resources object"
        )

    pool = resources.get("pool")

    if not isinstance(pool, dict):
        raise RuntimeError(
            "Bounded-pool response contains no pool state"
        )

    statistics = pool.get("statistics")

    if not isinstance(statistics, dict):
        raise RuntimeError(
            "Bounded-pool response contains no pool statistics"
        )

    return {
        "pool_size": int(statistics.get("pool_size", 0)),
        "pool_available": int(
            statistics.get("pool_available", 0)
        ),
        "requests_waiting": int(
            statistics.get("requests_waiting", 0)
        ),
        "requests_queued": int(
            statistics.get("requests_queued", 0)
        ),
    }


def build_base_row(
    *,
    run_id: str,
    workload_type: str,
    worker_number: int,
    sequence_number: int,
    request_number: int,
    request_id: str,
) -> dict[str, Any]:
    """Build fields shared by successful and failed requests."""

    return {
        "run_id": run_id,
        "workload_type": workload_type,
        "worker_number": worker_number,
        "sequence_number": sequence_number,
        "request_number": request_number,
        "request_id": request_id,
        "client_started_at_utc": utc_timestamp(),
    }


def build_failure_row(
    *,
    base_row: dict[str, Any],
    started: float,
    response: requests.Response | None,
    error: Exception,
) -> dict[str, Any]:
    """Build a consistent failed-request result row."""

    client_elapsed_ms = (
        time.perf_counter() - started
    ) * 1000

    return {
        **base_row,
        "client_finished_at_utc": utc_timestamp(),
        "client_elapsed_ms": round(client_elapsed_ms, 3),
        "status_code": (
            response.status_code
            if response is not None
            else ""
        ),
        "response_request_id": (
            response.headers.get("x-request-id", "")
            if response is not None
            else ""
        ),
        "outcome": "failure",
        "error_type": type(error).__name__,
        "error_message": str(error),
        "connection_strategy": "",
        "requested_batch_size": "",
        "selected_count": "",
        "updated_count": "",
        "audit_count": "",
        "encounter_ids": [],
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


def execute_foreground_worker(
    *,
    worker_number: int,
    configuration: MixedWorkloadConfiguration,
    run_id: str,
    barrier: threading.Barrier,
    api_base_url: str,
) -> list[dict[str, Any]]:
    """Execute latency-sensitive foreground patient requests."""

    rows: list[dict[str, Any]] = []

    endpoint = (
        f"{api_base_url}/qa/database-connection-timing"
    )

    with requests.Session() as session:
        barrier.wait()

        for sequence_number in range(
            1,
            configuration.foreground.requests_per_worker + 1,
        ):
            request_number = (
                (worker_number - 1)
                * configuration.foreground.requests_per_worker
                + sequence_number
            )

            request_id = (
                f"{run_id}-foreground-"
                f"worker{worker_number:02d}-"
                f"request{sequence_number:03d}"
            )

            base_row = build_base_row(
                run_id=run_id,
                workload_type="foreground",
                worker_number=worker_number,
                sequence_number=sequence_number,
                request_number=request_number,
                request_id=request_id,
            )

            started = time.perf_counter()
            response: requests.Response | None = None

            try:
                response = session.get(
                    endpoint,
                    params={
                        "patient_id": 1001,
                        "connection_hold_ms": (
                            configuration
                            .foreground_connection_hold_ms
                        ),
                    },
                    headers={"X-Request-ID": request_id},
                    timeout=(
                        configuration.connect_timeout_seconds,
                        configuration.read_timeout_seconds,
                    ),
                )

                client_elapsed_ms = (
                    time.perf_counter() - started
                ) * 1000

                response.raise_for_status()
                payload = response.json()

                actual_request_id = response.headers.get(
                    "x-request-id",
                    "",
                )

                if actual_request_id != request_id:
                    raise RuntimeError(
                        "Foreground request correlation mismatch: "
                        f"expected {request_id!r}, "
                        f"received {actual_request_id!r}"
                    )

                actual_strategy = payload.get(
                    "connection_strategy"
                )

                if actual_strategy != EXPECTED_CONNECTION_STRATEGY:
                    raise RuntimeError(
                        "Foreground connection strategy mismatch: "
                        f"expected {EXPECTED_CONNECTION_STRATEGY!r}, "
                        f"received {actual_strategy!r}"
                    )

                actual_hold_ms = payload.get(
                    "connection_hold_ms"
                )

                if (
                    actual_hold_ms
                    != configuration.foreground_connection_hold_ms
                ):
                    raise RuntimeError(
                        "Foreground connection hold mismatch: "
                        f"expected "
                        f"{configuration.foreground_connection_hold_ms!r}, "
                        f"received {actual_hold_ms!r}"
                    )

                timings = extract_database_timings(
                    payload,
                    field_name="database_phases",
                )

                pool = extract_pool_statistics(payload)

                rows.append(
                    {
                        **base_row,
                        "client_finished_at_utc": utc_timestamp(),
                        "client_elapsed_ms": round(
                            client_elapsed_ms,
                            3,
                        ),
                        "status_code": response.status_code,
                        "response_request_id": actual_request_id,
                        "outcome": "success",
                        "error_type": "",
                        "error_message": "",
                        "connection_strategy": actual_strategy,
                        "requested_batch_size": "",
                        "selected_count": "",
                        "updated_count": "",
                        "audit_count": "",
                        "encounter_ids": [],
                        "acquire_ms": timings["acquire_ms"],
                        "query_ms": timings["query_ms"],
                        "fetch_ms": timings["fetch_ms"],
                        "release_ms": timings["release_ms"],
                        "database_total_ms": timings["total_ms"],
                        **pool,
                    }
                )

            except Exception as error:
                rows.append(
                    build_failure_row(
                        base_row=base_row,
                        started=started,
                        response=response,
                        error=error,
                    )
                )

    return rows


def execute_background_worker(
    *,
    worker_number: int,
    configuration: MixedWorkloadConfiguration,
    run_id: str,
    barrier: threading.Barrier,
    api_base_url: str,
) -> list[dict[str, Any]]:
    """Execute transactional background encounter batches."""

    rows: list[dict[str, Any]] = []

    endpoint = (
        f"{api_base_url}/qa/background-encounter-batch"
    )

    worker_id = (
        f"{run_id}-background-worker{worker_number:02d}"
    )

    with requests.Session() as session:
        barrier.wait()

        for sequence_number in range(
            1,
            configuration.background.requests_per_worker + 1,
        ):
            request_number = (
                (worker_number - 1)
                * configuration.background.requests_per_worker
                + sequence_number
            )

            request_id = (
                f"{run_id}-background-"
                f"worker{worker_number:02d}-"
                f"request{sequence_number:03d}"
            )

            base_row = build_base_row(
                run_id=run_id,
                workload_type="background",
                worker_number=worker_number,
                sequence_number=sequence_number,
                request_number=request_number,
                request_id=request_id,
            )

            started = time.perf_counter()
            response: requests.Response | None = None

            try:
                response = session.post(
                    endpoint,
                    params={
                        "batch_size": (
                            configuration.background_batch_size
                        ),
                        "worker_id": worker_id,
                    },
                    headers={"X-Request-ID": request_id},
                    timeout=(
                        configuration.connect_timeout_seconds,
                        configuration.read_timeout_seconds,
                    ),
                )

                client_elapsed_ms = (
                    time.perf_counter() - started
                ) * 1000

                response.raise_for_status()
                payload = response.json()

                actual_request_id = response.headers.get(
                    "x-request-id",
                    "",
                )

                if actual_request_id != request_id:
                    raise RuntimeError(
                        "Background request correlation mismatch: "
                        f"expected {request_id!r}, "
                        f"received {actual_request_id!r}"
                    )

                if payload.get("batch_id") != request_id:
                    raise RuntimeError(
                        "Background batch correlation mismatch"
                    )

                if payload.get("worker_id") != worker_id:
                    raise RuntimeError(
                        "Background worker correlation mismatch"
                    )

                if (
                    payload.get("workload_type")
                    != "background_encounter_batch"
                ):
                    raise RuntimeError(
                        "Unexpected background workload type"
                    )

                actual_strategy = payload.get(
                    "connection_strategy"
                )

                if actual_strategy != EXPECTED_CONNECTION_STRATEGY:
                    raise RuntimeError(
                        "Background connection strategy mismatch: "
                        f"expected {EXPECTED_CONNECTION_STRATEGY!r}, "
                        f"received {actual_strategy!r}"
                    )

                expected_batch_size = (
                    configuration.background_batch_size
                )

                count_fields = (
                    "requested_batch_size",
                    "selected_count",
                    "updated_count",
                    "audit_count",
                )

                for field_name in count_fields:
                    if payload.get(field_name) != expected_batch_size:
                        raise RuntimeError(
                            f"Background {field_name} mismatch: "
                            f"expected {expected_batch_size!r}, "
                            f"received {payload.get(field_name)!r}"
                        )

                encounter_ids = payload.get("encounter_ids")

                if not isinstance(encounter_ids, list):
                    raise RuntimeError(
                        "Background response contains no encounter ID list"
                    )

                if len(encounter_ids) != expected_batch_size:
                    raise RuntimeError(
                        "Background encounter count mismatch"
                    )

                if len(set(encounter_ids)) != len(encounter_ids):
                    raise RuntimeError(
                        "Background response contains duplicate "
                        "encounter identifiers"
                    )

                timings = extract_database_timings(
                    payload,
                    field_name="database_timings",
                )

                pool = extract_pool_statistics(payload)

                rows.append(
                    {
                        **base_row,
                        "client_finished_at_utc": utc_timestamp(),
                        "client_elapsed_ms": round(
                            client_elapsed_ms,
                            3,
                        ),
                        "status_code": response.status_code,
                        "response_request_id": actual_request_id,
                        "outcome": "success",
                        "error_type": "",
                        "error_message": "",
                        "connection_strategy": actual_strategy,
                        "requested_batch_size": expected_batch_size,
                        "selected_count": payload["selected_count"],
                        "updated_count": payload["updated_count"],
                        "audit_count": payload["audit_count"],
                        "encounter_ids": encounter_ids,
                        "acquire_ms": timings["acquire_ms"],
                        "query_ms": timings["query_ms"],
                        "fetch_ms": timings["fetch_ms"],
                        "release_ms": timings["release_ms"],
                        "database_total_ms": timings["total_ms"],
                        **pool,
                    }
                )

            except Exception as error:
                rows.append(
                    build_failure_row(
                        base_row=base_row,
                        started=started,
                        response=response,
                        error=error,
                    )
                )

    return rows


def run_mixed_workload(
    *,
    configuration: MixedWorkloadConfiguration,
    run_id: str,
    api_base_url: str,
) -> tuple[list[dict[str, Any]], float]:
    """Run both workload types from one synchronized starting barrier."""

    barrier = threading.Barrier(
        configuration.total_concurrency
    )

    rows: list[dict[str, Any]] = []
    started = time.perf_counter()

    with ThreadPoolExecutor(
        max_workers=configuration.total_concurrency
    ) as executor:
        futures = []

        for worker_number in range(
            1,
            configuration.foreground.concurrency + 1,
        ):
            futures.append(
                executor.submit(
                    execute_foreground_worker,
                    worker_number=worker_number,
                    configuration=configuration,
                    run_id=run_id,
                    barrier=barrier,
                    api_base_url=api_base_url,
                )
            )

        for worker_number in range(
            1,
            configuration.background.concurrency + 1,
        ):
            futures.append(
                executor.submit(
                    execute_background_worker,
                    worker_number=worker_number,
                    configuration=configuration,
                    run_id=run_id,
                    barrier=barrier,
                    api_base_url=api_base_url,
                )
            )

        for future in as_completed(futures):
            rows.extend(future.result())

    elapsed_seconds = time.perf_counter() - started

    rows.sort(
        key=lambda row: (
            str(row["workload_type"]),
            int(row["request_number"]),
        )
    )

    return rows, elapsed_seconds


def summarize_smoke_run(
    rows: list[dict[str, Any]],
    *,
    elapsed_seconds: float,
) -> dict[str, Any]:
    """Build a compact console summary for the first live run."""

    summary: dict[str, Any] = {
        "elapsed_seconds": round(elapsed_seconds, 3),
    }

    for workload_type in ("foreground", "background"):
        matching_rows = [
            row
            for row in rows
            if row["workload_type"] == workload_type
        ]

        successful_rows = [
            row
            for row in matching_rows
            if row["outcome"] == "success"
        ]

        failed_rows = [
            row
            for row in matching_rows
            if row["outcome"] != "success"
        ]

        summary[workload_type] = {
            "request_count": len(matching_rows),
            "success_count": len(successful_rows),
            "failure_count": len(failed_rows),
            "client_elapsed_ms": metric_summary(
                [
                    float(row["client_elapsed_ms"])
                    for row in successful_rows
                ]
            ),
            "database_acquire_ms": metric_summary(
                [
                    float(row["acquire_ms"])
                    for row in successful_rows
                ]
            ),
            "failures": [
                {
                    "request_id": row["request_id"],
                    "error_type": row["error_type"],
                    "error_message": row["error_message"],
                }
                for row in failed_rows
            ],
        }

    return summary


def parse_arguments() -> argparse.Namespace:
    """Parse command-line settings for one mixed workload run."""

    parser = argparse.ArgumentParser(
        description=(
            "Run concurrent foreground API requests and background "
            "encounter batches through the same application."
        )
    )

    parser.add_argument(
        "--foreground-request-count",
        type=int,
        default=20,
    )
    parser.add_argument(
        "--foreground-concurrency",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--foreground-connection-hold-ms",
        type=int,
        default=0,
    )
    parser.add_argument(
        "--background-request-count",
        type=int,
        default=4,
    )
    parser.add_argument(
        "--background-concurrency",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--background-batch-size",
        type=int,
        default=2,
    )
    parser.add_argument(
        "--connect-timeout-seconds",
        type=float,
        default=3.0,
    )
    parser.add_argument(
        "--read-timeout-seconds",
        type=float,
        default=15.0,
    )

    return parser.parse_args()


def build_configuration(
    arguments: argparse.Namespace,
) -> MixedWorkloadConfiguration:
    """Build and validate an immutable study configuration."""

    configuration = MixedWorkloadConfiguration(
        foreground=WorkloadConfiguration(
            request_count=arguments.foreground_request_count,
            concurrency=arguments.foreground_concurrency,
        ),
        background=WorkloadConfiguration(
            request_count=arguments.background_request_count,
            concurrency=arguments.background_concurrency,
        ),
        foreground_connection_hold_ms=(
            arguments.foreground_connection_hold_ms
        ),
        background_batch_size=arguments.background_batch_size,
        connect_timeout_seconds=arguments.connect_timeout_seconds,
        read_timeout_seconds=arguments.read_timeout_seconds,
    )

    configuration.validate()

    return configuration


def display_configuration(
    configuration: MixedWorkloadConfiguration,
) -> None:
    """Display the validated workload settings."""

    print("FOREGROUND/BACKGROUND WORKLOAD CONFIGURATION")
    print("--------------------------------------------")
    print(
        "Foreground requests:",
        configuration.foreground.request_count,
    )
    print(
        "Foreground concurrency:",
        configuration.foreground.concurrency,
    )
    print(
        "Background requests:",
        configuration.background.request_count,
    )
    print(
        "Background concurrency:",
        configuration.background.concurrency,
    )
    print(
        "Background batch size:",
        configuration.background_batch_size,
    )
    print(
        "Required scheduled encounters:",
        configuration.required_encounter_count,
    )
    print(
        "Total concurrency:",
        configuration.total_concurrency,
    )


def main() -> int:
    """Prepare data, execute the mixed workload, and clean up."""

    arguments = parse_arguments()
    configuration = build_configuration(arguments)
    api_base_url = get_api_base_url()

    display_configuration(configuration)

    run_id = utc_now().strftime(
        "foreground-background-shared-pool-"
        "%Y%m%dT%H%M%S%fZ"
    )

    dataset: EncounterWorkloadDataset = build_workload_dataset(
        configuration.required_encounter_count
    )

    print()
    print("Preparing deterministic encounter data...")

    preparation = prepare_workload_dataset(dataset)

    print(
        "Prepared encounters:",
        preparation["verification"]["record_count"],
    )

    rows: list[dict[str, Any]] = []
    elapsed_seconds = 0.0

    try:
        print("Starting synchronized mixed workload...")

        rows, elapsed_seconds = run_mixed_workload(
            configuration=configuration,
            run_id=run_id,
            api_base_url=api_base_url,
        )
    finally:
        cleanup = remove_workload_dataset(dataset)

        print(
            "Cleaned encounters:",
            cleanup["encounters_deleted"],
        )
        print(
            "Cleaned audit rows:",
            cleanup["audit_rows_deleted"],
        )

    summary = summarize_smoke_run(
        rows,
        elapsed_seconds=elapsed_seconds,
    )

    print()
    print("MIXED WORKLOAD SMOKE RESULT")
    print("---------------------------")
    print("Run ID:", run_id)
    print("Elapsed seconds:", summary["elapsed_seconds"])

    for workload_type in ("foreground", "background"):
        workload_summary = summary[workload_type]

        print()
        print(workload_type.upper())
        print("Requests:", workload_summary["request_count"])
        print("Successes:", workload_summary["success_count"])
        print("Failures:", workload_summary["failure_count"])
        print(
            "Client p95 ms:",
            workload_summary[
                "client_elapsed_ms"
            ]["p95_ms"],
        )
        print(
            "Acquire p95 ms:",
            workload_summary[
                "database_acquire_ms"
            ]["p95_ms"],
        )

        for failure in workload_summary["failures"]:
            print(
                "Failure:",
                failure["request_id"],
                failure["error_type"],
                failure["error_message"],
            )

    total_failures = (
        summary["foreground"]["failure_count"]
        + summary["background"]["failure_count"]
    )

    return 0 if total_failures == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())