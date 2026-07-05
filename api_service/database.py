import os
from contextlib import contextmanager

import psycopg
from psycopg.rows import dict_row


DEFAULT_DATABASE_URL = "postgresql://sdet_user:sdet_password@localhost:5432/sdet_reliability"


def get_database_url() -> str:
    return os.getenv("DATABASE_URL", DEFAULT_DATABASE_URL)


@contextmanager
def get_connection():
    connection = psycopg.connect(
        get_database_url(),
        row_factory=dict_row,
    )

    try:
        yield connection
    finally:
        connection.close()
