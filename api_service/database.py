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

_foreground_database_pool: ConnectionPool | None = None
_background_database_pool: ConnectionPool | None = None
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


def _pool_is_open(pool: ConnectionPool | None) -> bool:
    return pool is not None and not pool.closed


def _create_database_pool(
    *,
    workload: str,
    name: str,
    application_name: str,
) -> ConnectionPool:
    configuration = get_database_pool_configuration(
        workload=workload,
    )

    pool = ConnectionPool(
        conninfo=get_database_url(),
        kwargs={
            "row_factory": dict_row,
            "application_name": application_name,
        },
        min_size=int(configuration["min_size"]),
        max_size=int(configuration["max_size"]),
        timeout=float(configuration["timeout_seconds"]),
        max_waiting=int(configuration["max_waiting"]),
        name=name,
        open=False,
    )

    try:
        pool.open(
            wait=True,
            timeout=float(
                configuration["startup_timeout_seconds"]
            ),
        )
    except Exception:
        pool.close()
        raise

    return pool


def _close_pool(pool: ConnectionPool | None) -> None:
    if pool is not None:
        pool.close()


def initialize_database_resources() -> None:
    global _foreground_database_pool
    global _background_database_pool

    if get_database_connection_strategy() != BOUNDED_POOL:
        return

    topology = get_database_pool_topology()

    with _database_pool_lock:
        foreground_is_ready = _pool_is_open(
            _foreground_database_pool
        )
        background_is_ready = _pool_is_open(
            _background_database_pool
        )

        if foreground_is_ready:
            if topology == SHARED_POOL and not background_is_ready:
                return

            if topology == ISOLATED_POOLS and background_is_ready:
                return

        _close_pool(_background_database_pool)
        _close_pool(_foreground_database_pool)
        _background_database_pool = None
        _foreground_database_pool = None

        try:
            _foreground_database_pool = _create_database_pool(
                workload=FOREGROUND_WORKLOAD,
                name="interactive-api-pool",
                application_name=(
                    "sdet-reliability-api-foreground-pool"
                ),
            )

            if topology == ISOLATED_POOLS:
                _background_database_pool = (
                    _create_database_pool(
                        workload=BACKGROUND_WORKLOAD,
                        name="background-worker-pool",
                        application_name=(
                            "sdet-reliability-api-background-pool"
                        ),
                    )
                )
        except Exception:
            _close_pool(_background_database_pool)
            _close_pool(_foreground_database_pool)
            _background_database_pool = None
            _foreground_database_pool = None
            raise


def close_database_resources() -> None:
    global _foreground_database_pool
    global _background_database_pool

    with _database_pool_lock:
        _close_pool(_background_database_pool)
        _close_pool(_foreground_database_pool)

        _background_database_pool = None
        _foreground_database_pool = None


def _require_database_pool(
    workload: str = FOREGROUND_WORKLOAD,
) -> ConnectionPool:
    resolved_workload = _validate_workload(workload)
    topology = get_database_pool_topology()

    if (
        topology == ISOLATED_POOLS
        and resolved_workload == BACKGROUND_WORKLOAD
    ):
        selected_pool = _background_database_pool
        selected_pool_name = "background"
    else:
        selected_pool = _foreground_database_pool
        selected_pool_name = "foreground"

    if selected_pool is None or selected_pool.closed:
        raise RuntimeError(
            f"The {selected_pool_name} bounded database pool "
            "is not initialized"
        )

    return selected_pool


def _pool_status(
    pool: ConnectionPool,
    *,
    workload: str,
) -> dict[str, Any]:
    return {
        "name": pool.name,
        "open": not pool.closed,
        "configuration": get_database_pool_configuration(
            workload=workload,
        ),
        "statistics": pool.get_stats(),
    }


def get_database_resource_status(
    workload: str = FOREGROUND_WORKLOAD,
) -> dict[str, Any]:
    strategy = get_database_connection_strategy()
    topology = get_database_pool_topology()
    resolved_workload = _validate_workload(workload)

    if strategy == CONNECTION_PER_OPERATION:
        return {
            "connection_strategy": strategy,
            "pool_topology": topology,
            "workload": resolved_workload,
            "pool": None,
        }

    pool = _require_database_pool(resolved_workload)

    pool_workload = (
        BACKGROUND_WORKLOAD
        if (
            topology == ISOLATED_POOLS
            and resolved_workload == BACKGROUND_WORKLOAD
        )
        else FOREGROUND_WORKLOAD
    )

    return {
        "connection_strategy": strategy,
        "pool_topology": topology,
        "workload": resolved_workload,
        "pool": _pool_status(
            pool,
            workload=pool_workload,
        ),
    }


@contextmanager
def get_connection(
    timings: DatabasePhaseTimings | None = None,
    *,
    workload: str = FOREGROUND_WORKLOAD,
) -> Iterator[psycopg.Connection]:
    total_started = time.perf_counter()
    acquire_started = time.perf_counter()
    release_started: float | None = None

    strategy = get_database_connection_strategy()
    resolved_workload = _validate_workload(workload)

    if strategy == BOUNDED_POOL:
        connection_context = _require_database_pool(
            resolved_workload,
        ).connection()
    else:
        application_name = (
            "sdet-reliability-api-background-direct"
            if resolved_workload == BACKGROUND_WORKLOAD
            else "sdet-reliability-api-foreground-direct"
        )

        connection_context = psycopg.connect(
            get_database_url(),
            row_factory=dict_row,
            application_name=application_name,
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