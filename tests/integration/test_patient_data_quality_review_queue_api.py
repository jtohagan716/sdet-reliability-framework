import shutil
import subprocess
from pathlib import Path

import pytest
import requests


REPO_ROOT = Path(__file__).resolve().parents[2]
STALE_MESSAGE_SCHEMA = REPO_ROOT / "db" / "sql" / "010_fhir_stale_message_evidence.sql"
REVIEW_QUEUE_SCHEMA = REPO_ROOT / "db" / "sql" / "011_patient_data_quality_review_queue.sql"
SEED_SCRIPT = REPO_ROOT / "scripts" / "seed_patient_data_quality_review_queue_api_demo.sql"

API_BASE_URL = "http://localhost:8000"
REVIEW_ITEM_KEY = "dq-review-api-encounter-example-001-stale-message"


def docker_is_available() -> bool:
    return shutil.which("docker") is not None


def postgres_service_is_available() -> bool:
    result = subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "pg_isready",
            "-U",
            "sdet_user",
            "-d",
            "sdet_reliability",
        ],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )

    return result.returncode == 0


def api_service_is_available() -> bool:
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    except requests.RequestException:
        return False

    return response.status_code == 200


def run_sql(script_contents: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            "docker",
            "compose",
            "exec",
            "-T",
            "postgres",
            "psql",
            "-U",
            "sdet_user",
            "-d",
            "sdet_reliability",
        ],
        cwd=REPO_ROOT,
        input=script_contents,
        capture_output=True,
        text=True,
        check=False,
    )


def apply_sql_file(sql_file: Path) -> None:
    assert sql_file.exists(), f"SQL file not found: {sql_file}"

    result = run_sql(sql_file.read_text(encoding="utf-8"))

    assert result.returncode == 0, result.stderr


@pytest.mark.integration
def test_patient_data_quality_review_queue_api_returns_review_items():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    if not api_service_is_available():
        pytest.skip("API service is not available.")

    apply_sql_file(STALE_MESSAGE_SCHEMA)
    apply_sql_file(REVIEW_QUEUE_SCHEMA)
    apply_sql_file(SEED_SCRIPT)

    response = requests.get(
        f"{API_BASE_URL}/qa/data-quality-review-items",
        params={
            "review_status": "confirmed_correct",
            "limit": 10,
        },
        timeout=10,
    )

    assert response.status_code == 200

    payload = response.json()

    assert "review_items" in payload
    assert payload["count"] >= 1

    matching_items = [
        item
        for item in payload["review_items"]
        if item["review_item_key"] == REVIEW_ITEM_KEY
    ]

    assert matching_items, "Expected seeded review item was not returned."

    review_item = matching_items[0]

    assert review_item["patient_reference"] == "Patient/example-patient-001"
    assert review_item["encounter_reference"] == "Encounter/example-encounter-api-review-001"
    assert review_item["review_status"] == "confirmed_correct"
    assert review_item["review_outcome"] == "software_decision_correct"
    assert review_item["assigned_role"] == "Data Quality Expert"


@pytest.mark.integration
def test_patient_data_quality_review_queue_api_returns_review_item_detail():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    if not api_service_is_available():
        pytest.skip("API service is not available.")

    apply_sql_file(STALE_MESSAGE_SCHEMA)
    apply_sql_file(REVIEW_QUEUE_SCHEMA)
    apply_sql_file(SEED_SCRIPT)

    response = requests.get(
        f"{API_BASE_URL}/qa/data-quality-review-items/{REVIEW_ITEM_KEY}",
        timeout=10,
    )

    assert response.status_code == 200

    payload = response.json()

    assert payload["review_item_key"] == REVIEW_ITEM_KEY
    assert payload["patient_reference"] == "Patient/example-patient-001"
    assert payload["encounter_reference"] == "Encounter/example-encounter-api-review-001"
    assert payload["review_status"] == "confirmed_correct"
    assert payload["review_outcome"] == "software_decision_correct"
    assert payload["assigned_role"] == "Data Quality Expert"

    assert "actions" in payload
    assert len(payload["actions"]) == 2

    action_types = [action["action_type"] for action in payload["actions"]]

    assert "created" in action_types
    assert "confirmed_correct" in action_types


@pytest.mark.integration
def test_patient_data_quality_review_queue_api_rejects_invalid_status():
    if not api_service_is_available():
        pytest.skip("API service is not available.")

    response = requests.get(
        f"{API_BASE_URL}/qa/data-quality-review-items",
        params={"review_status": "bad_status"},
        timeout=10,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "INVALID_REVIEW_STATUS"


@pytest.mark.integration
def test_patient_data_quality_review_queue_api_returns_404_for_missing_item():
    if not docker_is_available():
        pytest.skip("Docker is not available in this environment.")

    if not postgres_service_is_available():
        pytest.skip("PostgreSQL Docker service is not available.")

    if not api_service_is_available():
        pytest.skip("API service is not available.")

    apply_sql_file(STALE_MESSAGE_SCHEMA)
    apply_sql_file(REVIEW_QUEUE_SCHEMA)

    response = requests.get(
        f"{API_BASE_URL}/qa/data-quality-review-items/missing-review-item",
        timeout=10,
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "REVIEW_ITEM_NOT_FOUND"