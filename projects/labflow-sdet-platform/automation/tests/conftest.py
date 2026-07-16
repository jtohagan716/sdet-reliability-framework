import os
import uuid
from collections.abc import Generator
from pathlib import Path

import psycopg
import pytest
import requests
from psycopg import Connection
from psycopg.conninfo import make_conninfo

from automation.clients.health_client import HealthClient
from automation.clients.lab_orders_client import LabOrdersClient


def _read_environment_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()

        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", maxsplit=1)
        values[key.strip()] = value.strip().strip('"').strip("'")

    return values


@pytest.fixture(scope="session")
def base_url() -> str:
    configured_url = os.getenv(
        "LABFLOW_BASE_URL",
        "http://localhost:8000",
    )
    return configured_url.rstrip("/")


@pytest.fixture(scope="session")
def database_url() -> str:
    configured_url = os.getenv("LABFLOW_TEST_DATABASE_URL")

    if configured_url:
        return configured_url

    project_root = Path(__file__).resolve().parents[2]
    environment_file = project_root / ".env"

    if not environment_file.exists():
        pytest.fail(
            "Database tests require LABFLOW_TEST_DATABASE_URL "
            "or a LabFlow .env file."
        )

    environment = _read_environment_file(environment_file)

    required_keys = (
        "POSTGRES_DB",
        "POSTGRES_USER",
        "POSTGRES_PASSWORD",
    )
    missing_keys = [
        key
        for key in required_keys
        if not environment.get(key)
    ]

    if missing_keys:
        pytest.fail(
            "Missing required database settings: "
            + ", ".join(missing_keys)
        )

    return make_conninfo(
        host=os.getenv("LABFLOW_TEST_DB_HOST", "localhost"),
        port=os.getenv("LABFLOW_TEST_DB_PORT", "5433"),
        dbname=environment["POSTGRES_DB"],
        user=environment["POSTGRES_USER"],
        password=environment["POSTGRES_PASSWORD"],
        application_name="labflow-pytest",
        connect_timeout=5,
    )


@pytest.fixture
def db_connection(
    database_url: str,
) -> Generator[Connection, None, None]:
    connection = psycopg.connect(database_url)

    try:
        yield connection
    finally:
        connection.rollback()
        connection.close()


@pytest.fixture
def lab_order_payload():
    def build_payload(
        *,
        prefix="AUTO",
        synthetic_patient_id="SYN-PAT-AUTO",
        test_code="CBC",
        priority="ROUTINE",
        ordered_at="2026-07-15T18:00:00Z",
        include_priority=True,
        include_test_code=True,
    ):
        unique_suffix = uuid.uuid4().hex[:8]

        payload = {
            "placer_order_number": f"{prefix}-{unique_suffix}",
            "synthetic_patient_id": synthetic_patient_id,
            "ordered_at": ordered_at,
        }

        if include_test_code:
            payload["test_code"] = test_code

        if include_priority:
            payload["priority"] = priority

        return payload

    return build_payload


@pytest.fixture(scope="session")
def api_session():
    with requests.Session() as session:
        session.headers.update(
            {
                "Accept": "application/json",
            }
        )
        yield session


@pytest.fixture(scope="session")
def health_client(
    api_session,
    base_url,
):
    return HealthClient(
        session=api_session,
        base_url=base_url,
    )


@pytest.fixture(scope="session")
def lab_orders_client(
    api_session,
    base_url,
):
    return LabOrdersClient(
        session=api_session,
        base_url=base_url,
    )