from __future__ import annotations

import os
import threading
import time
from contextlib import contextmanager
from typing import Any, Iterator

import psycopg
from psycopg.rows import dict_row
from psycopg_pool import ConnectionPool

from api_service.database_timings import DatabasePhaseTimings


DEFAULT_DATABASE_URL = (
    "postgresql://sdet_user:sdet_password@"
    "localhost:5432/sdet_reliability"
)

CONNECTION_PER_OPERATION = "connection_per_operation"
BOUNDED_POOL = "bounded_pool"

SUPPORTED_CONNECTION_STRATEGIES = {
    CONNECTION_PER_OPERATION,
    BOUNDED_POOL,
}

SHARED_POOL = "shared_pool"
ISOLATED_POOLS = "isolated_pools"

SUPPORTED_POOL_TOPOLOGIES = {
    SHARED_POOL,
    ISOLATED_POOLS,
}

FOREGROUND_WORKLOAD = "foreground"
BACKGROUND_WORKLOAD = "background"

SUPPORTED_WORKLOADS = {
    FOREGROUND_WORKLOAD,
    BACKGROUND_WORKLOAD,
}

_database_pool: ConnectionPool | None = None
_database_pool_lock = threading.Lock()


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


def _get_int_setting(
    name: str,
    default: int,
    *,
    minimum: int,
) -> int:
    raw_value = os.getenv(name, str(default))

    try:
        value = int(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be an integer, received {raw_value!r}"
        ) from exc

    if value < minimum:
        raise ValueError(
            f"{name} must be at least {minimum}, received {value}"
        )

    return value


def _get_float_setting(
    name: str,
    default: float,
    *,
    minimum: float,
) -> float:
    raw_value = os.getenv(name, str(default))

    try:
        value = float(raw_value)
    except ValueError as exc:
        raise ValueError(
            f"{name} must be numeric, received {raw_value!r}"
        ) from exc

    if value < minimum:
        raise ValueError(
            f"{name} must be at least {minimum}, received {value}"
        )

    return value


def get_database_connection_strategy() -> str:
    strategy = os.getenv(
        "DATABASE_CONNECTION_STRATEGY",
        BOUNDED_POOL,
    ).strip().lower()

    if strategy not in SUPPORTED_CONNECTION_STRATEGIES:
        supported = ", ".join(
            sorted(SUPPORTED_CONNECTION_STRATEGIES)
        )

        raise ValueError(
            "Unsupported DATABASE_CONNECTION_STRATEGY "
            f"{strategy!r}. Supported values: {supported}"
        )

    return strategy


def get_database_pool_topology() -> str:
    topology = os.getenv(
        "DATABASE_POOL_TOPOLOGY",
        SHARED_POOL,
    ).strip().lower()

    if topology not in SUPPORTED_POOL_TOPOLOGIES:
        supported = ", ".join(
            sorted(SUPPORTED_POOL_TOPOLOGIES)
        )

        raise ValueError(
            "Unsupported DATABASE_POOL_TOPOLOGY "
            f"{topology!r}. Supported values: {supported}"
        )

    return topology


def _validate_workload(workload: str) -> str:
    resolved_workload = workload.strip().lower()

    if resolved_workload not in SUPPORTED_WORKLOADS:
        supported = ", ".join(sorted(SUPPORTED_WORKLOADS))

        raise ValueError(
            "Unsupported database workload "
            f"{resolved_workload!r}. Supported values: {supported}"
        )

    return resolved_workload


def get_database_pool_configuration(
    workload: str = FOREGROUND_WORKLOAD,
) -> dict[str, int | float]:
    resolved_workload = _validate_workload(workload)

    if resolved_workload == BACKGROUND_WORKLOAD:
        setting_prefix = "DB_BACKGROUND_POOL"
        default_minimum_size = 1
        default_maximum_size = 2
        default_timeout_seconds = 5.0
        default_startup_timeout_seconds = 30.0
        default_max_waiting = 10
    else:
        setting_prefix = "DB_POOL"
        default_minimum_size = 4
        default_maximum_size = 8
        default_timeout_seconds = 5.0
        default_startup_timeout_seconds = 30.0
        default_max_waiting = 40

    minimum_name = f"{setting_prefix}_MIN_SIZE"
    maximum_name = f"{setting_prefix}_MAX_SIZE"
    timeout_name = f"{setting_prefix}_TIMEOUT_SECONDS"
    startup_timeout_name = (
        f"{setting_prefix}_STARTUP_TIMEOUT_SECONDS"
    )
    max_waiting_name = f"{setting_prefix}_MAX_WAITING"

    minimum_size = _get_int_setting(
        minimum_name,
        default_minimum_size,
        minimum=1,
    )

    maximum_size = _get_int_setting(
        maximum_name,
        default_maximum_size,
        minimum=1,
    )

    if minimum_size > maximum_size:
        raise ValueError(
            f"{minimum_name} cannot exceed {maximum_name}"
        )

    return {
        "min_size": minimum_size,
        "max_size": maximum_size,
        "timeout_seconds": _get_float_setting(
            timeout_name,
            default_timeout_seconds,
            minimum=0.1,
        ),
        "startup_timeout_seconds": _get_float_setting(
            startup_timeout_name,
            default_startup_timeout_seconds,
            minimum=0.1,
        ),
        "max_waiting": _get_int_setting(
            max_waiting_name,
            default_max_waiting,
            minimum=0,
        ),
    }


def initialize_database_resources() -> None:
    global _database_pool

    if get_database_connection_strategy() != BOUNDED_POOL:
        return

    configuration = get_database_pool_configuration()

    with _database_pool_lock:
        if (
            _database_pool is not None
            and not _database_pool.closed
        ):
            return

        pool = ConnectionPool(
            conninfo=get_database_url(),
            kwargs={
                "row_factory": dict_row,
                "application_name": (
                    "sdet-reliability-api-bounded-pool"
                ),
            },
            min_size=int(configuration["min_size"]),
            max_size=int(configuration["max_size"]),
            timeout=float(
                configuration["timeout_seconds"]
            ),
            max_waiting=int(configuration["max_waiting"]),
            name="interactive-api-pool",
            open=False,
        )

        try:
            pool.open(
                wait=True,
                timeout=float(
                    configuration[
                        "startup_timeout_seconds"
                    ]
                ),
            )
        except Exception:
            pool.close()
            raise

        _database_pool = pool


def close_database_resources() -> None:
    global _database_pool

    with _database_pool_lock:
        if _database_pool is None:
            return

        _database_pool.close()
        _database_pool = None


def _require_database_pool() -> ConnectionPool:
    if _database_pool is None or _database_pool.closed:
        raise RuntimeError(
            "The bounded database pool is not initialized"
        )

    return _database_pool


def get_database_resource_status() -> dict[str, Any]:
    strategy = get_database_connection_strategy()

    if strategy == CONNECTION_PER_OPERATION:
        return {
            "connection_strategy": strategy,
            "pool": None,
        }

    pool = _require_database_pool()

    return {
        "connection_strategy": strategy,
        "pool": {
            "name": pool.name,
            "open": not pool.closed,
            "configuration": (
                get_database_pool_configuration()
            ),
            "statistics": pool.get_stats(),
        },
    }


@contextmanager
def get_connection(
    timings: DatabasePhaseTimings | None = None,
) -> Iterator[psycopg.Connection]:
    total_started = time.perf_counter()
    acquire_started = time.perf_counter()
    release_started: float | None = None

    strategy = get_database_connection_strategy()

    if strategy == BOUNDED_POOL:
        connection_context = (
            _require_database_pool().connection()
        )
    else:
        connection_context = psycopg.connect(
            get_database_url(),
            row_factory=dict_row,
            application_name=(
                "sdet-reliability-api-direct"
            ),
        )

    try:
        with connection_context as connection:
            if timings is not None:
                timings.acquire_ms = (
                    time.perf_counter() - acquire_started
                ) * 1000

            try:
                yield connection
            finally:
                release_started = time.perf_counter()

    finally:
        if timings is not None:
            if release_started is not None:
                timings.release_ms = (
                    time.perf_counter() - release_started
                ) * 1000

            timings.total_ms = (
                time.perf_counter() - total_started
            ) * 1000