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
        CONNECTION_PER_OPERATION,
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


def get_database_pool_configuration() -> dict[str, int | float]:
    minimum_size = _get_int_setting(
        "DB_POOL_MIN_SIZE",
        4,
        minimum=1,
    )

    maximum_size = _get_int_setting(
        "DB_POOL_MAX_SIZE",
        8,
        minimum=1,
    )

    if minimum_size > maximum_size:
        raise ValueError(
            "DB_POOL_MIN_SIZE cannot exceed DB_POOL_MAX_SIZE"
        )

    return {
        "min_size": minimum_size,
        "max_size": maximum_size,
        "timeout_seconds": _get_float_setting(
            "DB_POOL_TIMEOUT_SECONDS",
            5.0,
            minimum=0.1,
        ),
        "startup_timeout_seconds": _get_float_setting(
            "DB_POOL_STARTUP_TIMEOUT_SECONDS",
            30.0,
            minimum=0.1,
        ),
        "max_waiting": _get_int_setting(
            "DB_POOL_MAX_WAITING",
            40,
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
