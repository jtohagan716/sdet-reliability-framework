from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from api_service.database_timings import DatabasePhaseTimings


DEFAULT_DATABASE_URL = (
    "postgresql://sdet_user:sdet_password@"
    "localhost:5432/sdet_reliability"
)


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


@contextmanager
def get_connection(
    timings: DatabasePhaseTimings | None = None,
) -> Iterator[psycopg.Connection]:
    total_started = time.perf_counter()
    connect_started = time.perf_counter()

    connection = psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
    )

    if timings is not None:
        timings.connect_ms = (
            time.perf_counter() - connect_started
        ) * 1000

    try:
        yield connection
    finally:
        close_started = time.perf_counter()
        connection.close()

        if timings is not None:
            timings.close_ms = (
                time.perf_counter() - close_started
            ) * 1000

            timings.total_ms = (
                time.perf_counter() - total_started
            ) * 1000
