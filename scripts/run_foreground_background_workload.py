from __future__ import annotations

import argparse
import csv
import json
import math
import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import asdict, dataclass
from datetime import UTC, date, datetime
from pathlib import Path
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


REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
TEST_RUNS_DIRECTORY = REPOSITORY_ROOT / "reports" / "test-runs"

DEFAULT_API_BASE_URL = "http://localhost:8000"
EXPECTED_CONNECTION_STRATEGY = "bounded_pool"
SUPPORTED_POOL_TOPOLOGIES = (
    "shared_pool",
    "isolated_pools",
)


def build_scenario_name(pool_topology: str) -> str:
    """Build an evidence scenario name for one pool topology."""

    if pool_topology not in SUPPORTED_POOL_TOPOLOGIES:
        raise ValueError(
            f"Unsupported database pool topology: {pool_topology}"
        )

    return f"{pool_topology}_mixed_workload"


def build_run_id(
    *,
    pool_topology: str,
    generated_at: datetime,
) -> str:
    """Build a deterministic topology-aware workload run identifier."""

    if pool_topology not in SUPPORTED_POOL_TOPOLOGIES:
        raise ValueError(
            f"Unsupported database pool topology: {pool_topology}"
        )

    topology_label = pool_topology.replace("_", "-")
    timestamp = generated_at.strftime("%Y%m%dT%H%M%S%fZ")

    return (
        f"foreground-background-{topology_label}-"
        f"{timestamp}"
    )

DATABASE_PHASE_NAMES = (
    "acquire_ms",
    "query_ms",
    "fetch_ms",
    "release_ms",
    "total_ms",
)

CSV_FIELD_NAMES = (
    "run_id",
    "workload_type",
    "worker_number",
    "sequence_number",
    "request_phase",
    "request_number",
    "request_id",
    "client_started_at_utc",
    "client_finished_at_utc",
    "client_elapsed_ms",
    "status_code",
    "response_request_id",
    "outcome",
    "error_type",
    "error_message",
    "connection_strategy",
    "requested_batch_size",
    "selected_count",
    "updated_count",
    "audit_count",
    "encounter_ids",
    "trace_id",
    "span_id",
    "acquire_ms",
    "query_ms",
    "fetch_ms",
    "release_ms",
    "database_total_ms",
    "pool_size",
    "pool_available",
    "requests_waiting",
    "requests_queued",
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

    expected_pool_topology: str
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


def classify_request_phase(
    sequence_number: int,
) -> str:
    """Classify a worker request as first-wave or later work."""

    if sequence_number <= 0:
        raise ValueError(
            "sequence number must be greater than zero"
        )

    if sequence_number == 1:
        return "first_request"

    return "later_requests"


def average_metric(
    values: list[float],
) -> float | None:
    """Return a three-decimal arithmetic mean."""

    if not values:
        return None

    return round(sum(values) / len(values), 3)


def summarize_request_phase_rows(
    rows: list[dict[str, Any]],
) -> dict[str, float | int | None]:
    """Summarize client, database, and outside-database latency."""

    client_values = [
        float(row["client_elapsed_ms"])
        for row in rows
    ]

    database_values = [
        float(row["database_total_ms"])
        for row in rows
    ]

    outside_database_values = [
        round(
            float(row["client_elapsed_ms"])
            - float(row["database_total_ms"]),
            3,
        )
        for row in rows
    ]

    return {
        "count": len(rows),
        "average_client_ms": average_metric(client_values),
        "average_database_ms": average_metric(database_values),
        "average_outside_database_ms": average_metric(
            outside_database_values
        ),
    }


def summarize_request_phases(
    rows: list[dict[str, Any]],
) -> dict[str, dict[str, dict[str, float | int | None]]]:
    """Separate first requests from later steady-state requests."""

    summary: dict[
        str,
        dict[str, dict[str, float | int | None]],
    ] = {}

    for workload_type in ("foreground", "background"):
        successful_rows = [
            row
            for row in rows
            if row.get("workload_type") == workload_type
            and row.get("outcome") == "success"
        ]

        first_request_rows = [
            row
            for row in successful_rows
            if classify_request_phase(
                int(row["sequence_number"])
            )
            == "first_request"
        ]

        later_request_rows = [
            row
            for row in successful_rows
            if classify_request_phase(
                int(row["sequence_number"])
            )
            == "later_requests"
        ]

        summary[workload_type] = {
            "first_request": summarize_request_phase_rows(
                first_request_rows
            ),
            "later_requests": summarize_request_phase_rows(
                later_request_rows
            ),
        }

    return summary


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


def validate_pool_topology(
    *,
    expected_pool_topology: str,
    observed_pool_topology: str,
) -> None:
    """Reject evidence collected from an unexpected pool topology."""

    if observed_pool_topology != expected_pool_topology:
        raise RuntimeError(
            "Expected database pool topology "
            f"'{expected_pool_topology}', "
            "but the API reported "
            f"'{observed_pool_topology}'"
        )


def extract_pool_statistics(
    payload: dict[str, Any],
    *,
    expected_pool_topology: str | None = None,
) -> dict[str, int | None]:
    """Validate and return the bounded-pool statistics."""

    resources = payload.get("database_resources")

    if not isinstance(resources, dict):
        raise RuntimeError(
            "Response contains no database_resources object"
        )

    if expected_pool_topology is not None:
        validate_pool_topology(
            expected_pool_topology=expected_pool_topology,
            observed_pool_topology=str(
                resources.get("pool_topology", "")
            ),
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
        "requests_queued": (
            int(statistics["requests_queued"])
            if statistics.get("requests_queued") is not None
            else None
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
        "request_phase": classify_request_phase(sequence_number),
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
        "trace_id": "",
        "span_id": "",
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

                pool = extract_pool_statistics(
                    payload,
                    expected_pool_topology=(
                        configuration.expected_pool_topology
                    ),
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
                        "trace_id": payload.get("trace_id", ""),
                        "span_id": payload.get("span_id", ""),
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

                pool = extract_pool_statistics(
                    payload,
                    expected_pool_topology=(
                        configuration.expected_pool_topology
                    ),
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
                        "trace_id": payload.get("trace_id", ""),
                        "span_id": payload.get("span_id", ""),
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


def successful_metric_values(
    rows: list[dict[str, Any]],
    field_name: str,
) -> list[float]:
    """Return successful numeric measurements for one field."""

    values: list[float] = []

    for row in rows:
        if row.get("outcome") != "success":
            continue

        value = row.get(field_name)

        if value in ("", None):
            continue

        values.append(float(value))

    return values


def integer_observations(
    rows: list[dict[str, Any]],
    field_name: str,
) -> list[int]:
    """Return successful integer observations for one field."""

    values: list[int] = []

    for row in rows:
        if row.get("outcome") != "success":
            continue

        value = row.get(field_name)

        if value in ("", None):
            continue

        values.append(int(value))

    return values


def summarize_workload(
    rows: list[dict[str, Any]],
    *,
    workload_type: str,
    elapsed_seconds: float,
) -> dict[str, Any]:
    """Build a complete summary for one workload type."""

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

    pool_sizes = integer_observations(
        successful_rows,
        "pool_size",
    )

    pool_available = integer_observations(
        successful_rows,
        "pool_available",
    )

    requests_waiting = integer_observations(
        successful_rows,
        "requests_waiting",
    )

    requests_queued = integer_observations(
        successful_rows,
        "requests_queued",
    )

    selected_count = sum(
        int(row["selected_count"])
        for row in successful_rows
        if row["selected_count"] not in ("", None)
    )

    updated_count = sum(
        int(row["updated_count"])
        for row in successful_rows
        if row["updated_count"] not in ("", None)
    )

    audit_count = sum(
        int(row["audit_count"])
        for row in successful_rows
        if row["audit_count"] not in ("", None)
    )

    return {
        "request_count": len(matching_rows),
        "success_count": len(successful_rows),
        "failure_count": len(failed_rows),
        "success_rate_percent": (
            round(
                100 * len(successful_rows) / len(matching_rows),
                3,
            )
            if matching_rows
            else 0.0
        ),
        "throughput_requests_per_second": (
            round(len(matching_rows) / elapsed_seconds, 3)
            if elapsed_seconds > 0
            else 0.0
        ),
        "metrics": {
            "client_elapsed_ms": metric_summary(
                successful_metric_values(
                    successful_rows,
                    "client_elapsed_ms",
                )
            ),
            "database_acquire_ms": metric_summary(
                successful_metric_values(
                    successful_rows,
                    "acquire_ms",
                )
            ),
            "database_query_ms": metric_summary(
                successful_metric_values(
                    successful_rows,
                    "query_ms",
                )
            ),
            "database_fetch_ms": metric_summary(
                successful_metric_values(
                    successful_rows,
                    "fetch_ms",
                )
            ),
            "database_release_ms": metric_summary(
                successful_metric_values(
                    successful_rows,
                    "release_ms",
                )
            ),
            "database_total_ms": metric_summary(
                successful_metric_values(
                    successful_rows,
                    "database_total_ms",
                )
            ),
        },
        "pool_observations": {
            "peak_pool_size": (
                max(pool_sizes)
                if pool_sizes
                else None
            ),
            "minimum_pool_available": (
                min(pool_available)
                if pool_available
                else None
            ),
            "peak_requests_waiting": (
                max(requests_waiting)
                if requests_waiting
                else None
            ),
            "peak_requests_queued": (
                max(requests_queued)
                if requests_queued
                else None
            ),
        },
        "database_work": {
            "selected_count": selected_count,
            "updated_count": updated_count,
            "audit_count": audit_count,
        },
        "failures": [
            {
                "request_id": row["request_id"],
                "status_code": row["status_code"],
                "error_type": row["error_type"],
                "error_message": row["error_message"],
            }
            for row in failed_rows
        ],
    }


def summarize_run(
    rows: list[dict[str, Any]],
    *,
    elapsed_seconds: float,
) -> dict[str, Any]:
    """Build the complete mixed-workload run summary."""

    foreground = summarize_workload(
        rows,
        workload_type="foreground",
        elapsed_seconds=elapsed_seconds,
    )

    background = summarize_workload(
        rows,
        workload_type="background",
        elapsed_seconds=elapsed_seconds,
    )

    return {
        "elapsed_seconds": round(elapsed_seconds, 3),
        "total_request_count": len(rows),
        "total_success_count": (
            foreground["success_count"]
            + background["success_count"]
        ),
        "total_failure_count": (
            foreground["failure_count"]
            + background["failure_count"]
        ),
        "foreground": foreground,
        "background": background,
        "request_phases": summarize_request_phases(rows),
    }


def configuration_to_dict(
    configuration: MixedWorkloadConfiguration,
) -> dict[str, Any]:
    """Convert the immutable configuration to report data."""

    return {
        "foreground": {
            **asdict(configuration.foreground),
            "requests_per_worker": (
                configuration.foreground.requests_per_worker
            ),
            "connection_hold_ms": (
                configuration.foreground_connection_hold_ms
            ),
        },
        "background": {
            **asdict(configuration.background),
            "requests_per_worker": (
                configuration.background.requests_per_worker
            ),
            "batch_size": configuration.background_batch_size,
            "required_encounter_count": (
                configuration.required_encounter_count
            ),
        },
        "combined": {
            "total_concurrency": (
                configuration.total_concurrency
            ),
            "connect_timeout_seconds": (
                configuration.connect_timeout_seconds
            ),
            "read_timeout_seconds": (
                configuration.read_timeout_seconds
            ),
        },
    }


def dataset_to_dict(
    dataset: EncounterWorkloadDataset,
) -> dict[str, Any]:
    """Convert the deterministic dataset definition to report data."""

    return {
        "encounter_ids": list(dataset.encounter_ids),
        "record_count": dataset.record_count,
        "encounter_date": dataset.encounter_date.isoformat(),
        "encounter_type": dataset.encounter_type,
    }


def json_safe(value: Any) -> Any:
    """Convert report values to JSON-compatible types."""

    if isinstance(value, dict):
        return {
            str(key): json_safe(item)
            for key, item in value.items()
        }

    if isinstance(value, (list, tuple, set)):
        return [
            json_safe(item)
            for item in value
        ]

    if isinstance(value, (datetime, date)):
        return value.isoformat()

    if isinstance(value, Path):
        return str(value)

    return value


def csv_safe(value: Any) -> Any:
    """Convert structured row values to stable CSV text."""

    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(
            json_safe(value),
            sort_keys=True,
            separators=(",", ":"),
        )

    if value is None:
        return ""

    return value


def create_run_directory(run_id: str) -> Path:
    """Create one isolated artifact directory for the run."""

    run_directory = TEST_RUNS_DIRECTORY / run_id
    run_directory.mkdir(parents=True, exist_ok=False)

    return run_directory


def write_request_csv(
    run_directory: Path,
    rows: list[dict[str, Any]],
) -> Path:
    """Write one raw request row per HTTP operation."""

    output_path = run_directory / "request-results.csv"

    with output_path.open(
        "w",
        encoding="utf-8",
        newline="",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=CSV_FIELD_NAMES,
            extrasaction="ignore",
        )

        writer.writeheader()

        for row in rows:
            writer.writerow(
                {
                    field_name: csv_safe(
                        row.get(field_name, "")
                    )
                    for field_name in CSV_FIELD_NAMES
                }
            )

    return output_path


def write_json_report(
    run_directory: Path,
    report: dict[str, Any],
) -> Path:
    """Write the complete machine-readable run report."""

    output_path = run_directory / "run-report.json"

    output_path.write_text(
        json.dumps(
            json_safe(report),
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return output_path


def format_markdown_value(value: Any) -> str:
    """Format one report value for a Markdown table."""

    if value is None:
        return "n/a"

    if isinstance(value, float):
        return f"{value:.3f}"

    return str(value)


def metric_markdown_rows(
    metrics: dict[str, dict[str, Any]],
) -> list[str]:
    """Build Markdown table rows for latency metrics."""

    display_names = {
        "client_elapsed_ms": "Client elapsed",
        "database_acquire_ms": "Database acquire",
        "database_query_ms": "Database query",
        "database_fetch_ms": "Database fetch",
        "database_release_ms": "Database release",
        "database_total_ms": "Database total",
    }

    rows = [
        "| Metric | Count | Min ms | Mean ms | "
        "P50 ms | P95 ms | P99 ms | Max ms |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for metric_name, summary in metrics.items():
        rows.append(
            "| "
            + " | ".join(
                [
                    display_names.get(
                        metric_name,
                        metric_name,
                    ),
                    format_markdown_value(
                        summary["count"]
                    ),
                    format_markdown_value(
                        summary["minimum_ms"]
                    ),
                    format_markdown_value(
                        summary["mean_ms"]
                    ),
                    format_markdown_value(
                        summary["p50_ms"]
                    ),
                    format_markdown_value(
                        summary["p95_ms"]
                    ),
                    format_markdown_value(
                        summary["p99_ms"]
                    ),
                    format_markdown_value(
                        summary["maximum_ms"]
                    ),
                ]
            )
            + " |"
        )

    return rows


def request_phase_markdown_section(
    request_phases: dict[str, Any],
) -> list[str]:
    """Build first-request and later-request comparison tables."""

    lines = [
        "## First-request versus later-request behavior",
        "",
        (
            "The first request from each worker is reported separately "
            "from later requests so first-use overhead does not obscure "
            "steady-state behavior."
        ),
        "",
        "| Workload | Phase | Count | Average client ms | "
        "Average database ms | Average outside-database ms |",
        "|---|---|---:|---:|---:|---:|",
    ]

    for workload_type in ("foreground", "background"):
        for phase_name in (
            "first_request",
            "later_requests",
        ):
            phase_summary = request_phases[
                workload_type
            ][phase_name]

            lines.append(
                "| "
                + " | ".join(
                    [
                        workload_type.capitalize(),
                        phase_name,
                        format_markdown_value(
                            phase_summary["count"]
                        ),
                        format_markdown_value(
                            phase_summary["average_client_ms"]
                        ),
                        format_markdown_value(
                            phase_summary["average_database_ms"]
                        ),
                        format_markdown_value(
                            phase_summary[
                                "average_outside_database_ms"
                            ]
                        ),
                    ]
                )
                + " |"
            )

    return lines


def workload_markdown_section(
    workload_name: str,
    summary: dict[str, Any],
) -> list[str]:
    """Build one workload section for the Markdown report."""

    title = workload_name.capitalize()

    lines = [
        f"## {title} workload",
        "",
        f"- Requests: {summary['request_count']}",
        f"- Successes: {summary['success_count']}",
        f"- Failures: {summary['failure_count']}",
        (
            "- Success rate: "
            f"{summary['success_rate_percent']:.3f}%"
        ),
        (
            "- Observed completion rate: "
            f"{summary['throughput_requests_per_second']:.3f} "
            "requests/second during the combined run"
        ),
        "",
        "### Latency distribution",
        "",
        *metric_markdown_rows(summary["metrics"]),
        "",
        "### Connection-pool observations",
        "",
        (
            "- Peak reported pool size: "
            + format_markdown_value(
                summary["pool_observations"]["peak_pool_size"]
            )
        ),
        (
            "- Minimum reported available connections: "
            + format_markdown_value(
                summary["pool_observations"][
                    "minimum_pool_available"
                ]
            )
        ),
        (
            "- Peak reported requests waiting: "
            + format_markdown_value(
                summary["pool_observations"][
                    "peak_requests_waiting"
                ]
            )
        ),
        (
            "- Peak reported requests queued: "
            + format_markdown_value(
                summary["pool_observations"][
                    "peak_requests_queued"
                ]
            )
        ),
    ]

    if workload_name == "background":
        database_work = summary["database_work"]

        lines.extend(
            [
                "",
                "### Transactional work",
                "",
                (
                    "- Encounters selected: "
                    f"{database_work['selected_count']}"
                ),
                (
                    "- Encounters updated: "
                    f"{database_work['updated_count']}"
                ),
                (
                    "- Audit rows validated: "
                    f"{database_work['audit_count']}"
                ),
            ]
        )

    if summary["failures"]:
        lines.extend(
            [
                "",
                "### Failures",
                "",
            ]
        )

        for failure in summary["failures"]:
            lines.append(
                "- "
                f"`{failure['request_id']}`: "
                f"{failure['error_type']} — "
                f"{failure['error_message']}"
            )

    return lines


def write_markdown_report(
    run_directory: Path,
    report: dict[str, Any],
) -> Path:
    """Write the human-readable experiment report."""

    configuration = report["configuration"]
    summary = report["summary"]
    cleanup = report["cleanup"]

    lines = [
        "# Foreground vs. Background Workload Run",
        "",
        f"- Run ID: `{report['run_id']}`",
        f"- Scenario: `{report['scenario']}`",
        f"- API base URL: `{report['api_base_url']}`",
        (
            "- Connection strategy expected: "
            f"`{report['expected_connection_strategy']}`"
        ),
        (
            "- Started UTC: "
            f"`{report['execution']['started_at_utc']}`"
        ),
        (
            "- Finished UTC: "
            f"`{report['execution']['finished_at_utc']}`"
        ),
        (
            "- Elapsed seconds: "
            f"{summary['elapsed_seconds']:.3f}"
        ),
        "",
        "## Purpose",
        "",
        (
            "Measure latency-sensitive foreground API requests and "
            "transactional background encounter batches while both "
            "use the same bounded database connection pool."
        ),
        "",
        "## Configuration",
        "",
        "| Setting | Value |",
        "|---|---:|",
        (
            "| Foreground requests | "
            f"{configuration['foreground']['request_count']} |"
        ),
        (
            "| Foreground concurrency | "
            f"{configuration['foreground']['concurrency']} |"
        ),
        (
            "| Foreground requests per worker | "
            f"{configuration['foreground']['requests_per_worker']} |"
        ),
        (
            "| Foreground connection hold ms | "
            f"{configuration['foreground']['connection_hold_ms']} |"
        ),
        (
            "| Background requests | "
            f"{configuration['background']['request_count']} |"
        ),
        (
            "| Background concurrency | "
            f"{configuration['background']['concurrency']} |"
        ),
        (
            "| Background requests per worker | "
            f"{configuration['background']['requests_per_worker']} |"
        ),
        (
            "| Background batch size | "
            f"{configuration['background']['batch_size']} |"
        ),
        (
            "| Required encounters | "
            f"{configuration['background']['required_encounter_count']} |"
        ),
        (
            "| Total concurrency | "
            f"{configuration['combined']['total_concurrency']} |"
        ),
        (
            "| Connect timeout seconds | "
            f"{configuration['combined']['connect_timeout_seconds']} |"
        ),
        (
            "| Read timeout seconds | "
            f"{configuration['combined']['read_timeout_seconds']} |"
        ),
        "",
        "## Overall result",
        "",
        f"- Total requests: {summary['total_request_count']}",
        f"- Total successes: {summary['total_success_count']}",
        f"- Total failures: {summary['total_failure_count']}",
        (
            "- Fatal runner error: "
            f"{report['execution']['fatal_error'] or 'none'}"
        ),
        "",
        *request_phase_markdown_section(
            summary["request_phases"]
        ),
        "",
        *workload_markdown_section(
            "foreground",
            summary["foreground"],
        ),
        "",
        *workload_markdown_section(
            "background",
            summary["background"],
        ),
        "",
        "## Deterministic data lifecycle",
        "",
        (
            "- Prepared encounter count: "
            f"{report['dataset']['record_count']}"
        ),
        (
            "- Cleanup encounters deleted: "
            f"{cleanup.get('encounters_deleted', 'n/a')}"
        ),
        (
            "- Cleanup audit rows deleted: "
            f"{cleanup.get('audit_rows_deleted', 'n/a')}"
        ),
        (
            "- Cleanup error: "
            f"{report['cleanup_error'] or 'none'}"
        ),
        "",
        "## Interpretation boundary",
        "",
        (
            "This individual run proves whether the configured mixed "
            "workload completed correctly and records observed timing "
            "and pool behavior. It does not, by itself, prove that "
            "background activity caused foreground latency. Causal "
            "claims require repeated foreground-only, shared-pool, "
            "and isolated-pool comparisons under controlled settings."
        ),
        "",
        "## Artifacts",
        "",
        "- `request-results.csv`: one row per HTTP request",
        "- `run-report.json`: complete machine-readable evidence",
        "- `run-report.md`: this human-readable report",
        "",
    ]

    output_path = run_directory / "run-report.md"

    output_path.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    return output_path


def write_run_artifacts(
    *,
    run_directory: Path,
    rows: list[dict[str, Any]],
    report: dict[str, Any],
) -> dict[str, Path]:
    """Write all evidence files for one experiment run."""

    csv_path = write_request_csv(
        run_directory,
        rows,
    )

    json_path = write_json_report(
        run_directory,
        report,
    )

    markdown_path = write_markdown_report(
        run_directory,
        report,
    )

    return {
        "run_directory": run_directory,
        "request_csv": csv_path,
        "json_report": json_path,
        "markdown_report": markdown_path,
    }


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
    parser.add_argument(
        "--expected-pool-topology",
        choices=SUPPORTED_POOL_TOPOLOGIES,
        default="shared_pool",
        help=(
            "Database pool topology the API must report during the run. "
            "Defaults to shared_pool."
        ),
    )

    return parser.parse_args()



def build_configuration(
    arguments: argparse.Namespace,
) -> MixedWorkloadConfiguration:
    """Build and validate an immutable study configuration."""

    configuration = MixedWorkloadConfiguration(
        expected_pool_topology=arguments.expected_pool_topology,
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
        "Expected pool topology:",
        configuration.expected_pool_topology,
    )
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


def display_summary(
    *,
    run_id: str,
    summary: dict[str, Any],
    artifact_paths: dict[str, Path],
    fatal_error: str,
    cleanup_error: str,
) -> None:
    """Display the compact console result and artifact locations."""

    print()
    print("MIXED WORKLOAD RESULT")
    print("---------------------")
    print("Run ID:", run_id)
    print("Elapsed seconds:", summary["elapsed_seconds"])

    for workload_type in ("foreground", "background"):
        workload_summary = summary[workload_type]
        metrics = workload_summary["metrics"]

        print()
        print(workload_type.upper())
        print("Requests:", workload_summary["request_count"])
        print("Successes:", workload_summary["success_count"])
        print("Failures:", workload_summary["failure_count"])
        print(
            "Client p50 ms:",
            metrics["client_elapsed_ms"]["p50_ms"],
        )
        print(
            "Client p95 ms:",
            metrics["client_elapsed_ms"]["p95_ms"],
        )
        print(
            "Acquire p95 ms:",
            metrics["database_acquire_ms"]["p95_ms"],
        )
        print(
            "Database total p95 ms:",
            metrics["database_total_ms"]["p95_ms"],
        )

        for failure in workload_summary["failures"]:
            print(
                "Failure:",
                failure["request_id"],
                failure["error_type"],
                failure["error_message"],
            )

    if fatal_error:
        print()
        print("Fatal runner error:", fatal_error)

    if cleanup_error:
        print()
        print("Cleanup error:", cleanup_error)

    print()
    print("ARTIFACTS")
    print("---------")
    print("Run directory:", artifact_paths["run_directory"])
    print("Request CSV:", artifact_paths["request_csv"])
    print("JSON report:", artifact_paths["json_report"])
    print("Markdown report:", artifact_paths["markdown_report"])


def main() -> int:
    """Prepare data, execute the workload, and persist evidence."""

    arguments = parse_arguments()
    configuration = build_configuration(arguments)
    api_base_url = get_api_base_url()

    display_configuration(configuration)

    run_id = build_run_id(
        pool_topology=configuration.expected_pool_topology,
        generated_at=utc_now(),
    )

    run_directory = create_run_directory(run_id)

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
    fatal_error = ""
    cleanup_error = ""
    cleanup: dict[str, Any] = {}

    execution_started_at_utc = utc_timestamp()

    try:
        print("Starting synchronized mixed workload...")

        rows, elapsed_seconds = run_mixed_workload(
            configuration=configuration,
            run_id=run_id,
            api_base_url=api_base_url,
        )
    except Exception as error:
        fatal_error = (
            f"{type(error).__name__}: {error}"
        )
    finally:
        try:
            cleanup = remove_workload_dataset(dataset)

            print(
                "Cleaned encounters:",
                cleanup["encounters_deleted"],
            )
            print(
                "Cleaned audit rows:",
                cleanup["audit_rows_deleted"],
            )
        except Exception as error:
            cleanup_error = (
                f"{type(error).__name__}: {error}"
            )

    execution_finished_at_utc = utc_timestamp()

    summary = summarize_run(
        rows,
        elapsed_seconds=elapsed_seconds,
    )

    report = {
        "run_id": run_id,
        "scenario": build_scenario_name(
            configuration.expected_pool_topology
        ),
        "generated_at_utc": utc_timestamp(),
        "api_base_url": api_base_url,
        "expected_connection_strategy": (
            EXPECTED_CONNECTION_STRATEGY
        ),
        "configuration": configuration_to_dict(
            configuration
        ),
        "dataset": dataset_to_dict(dataset),
        "preparation": preparation,
        "execution": {
            "started_at_utc": execution_started_at_utc,
            "finished_at_utc": execution_finished_at_utc,
            "elapsed_seconds": round(
                elapsed_seconds,
                3,
            ),
            "fatal_error": fatal_error,
        },
        "summary": summary,
        "cleanup": cleanup,
        "cleanup_error": cleanup_error,
        "request_rows": rows,
    }

    artifact_paths = write_run_artifacts(
        run_directory=run_directory,
        rows=rows,
        report=report,
    )

    display_summary(
        run_id=run_id,
        summary=summary,
        artifact_paths=artifact_paths,
        fatal_error=fatal_error,
        cleanup_error=cleanup_error,
    )

    total_failures = summary["total_failure_count"]

    if fatal_error or cleanup_error or total_failures:
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())