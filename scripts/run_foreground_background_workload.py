from __future__ import annotations

import argparse
import math
import os
from dataclasses import dataclass
from datetime import UTC, datetime
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
        """Return the number of scheduled encounters required by the run."""

        return (
            self.background.request_count
            * self.background_batch_size
        )

    @property
    def total_concurrency(self) -> int:
        """Return the combined number of foreground and background workers."""

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


def main() -> int:
    """Validate and display the requested mixed workload configuration."""

    arguments = parse_arguments()
    configuration = build_configuration(arguments)

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

    return 0


if __name__ == "__main__":
    raise SystemExit(main())