from types import SimpleNamespace

import api_service.app as app_module
from api_service.database import BACKGROUND_WORKLOAD


def test_background_endpoint_reports_background_database_resources(
    monkeypatch,
):
    monkeypatch.setenv("ENABLE_QA_ENDPOINTS", "true")

    def fake_process_scheduled_encounter_batch(
        *,
        batch_size,
        worker_id,
        batch_id,
        timings,
    ):
        return {
            "batch_id": batch_id,
            "worker_id": worker_id,
            "requested_batch_size": batch_size,
            "selected_count": 2,
            "updated_count": 2,
            "audit_count": 2,
            "encounter_ids": [1001, 1002],
            "status_transition": {
                "from": "scheduled",
                "to": "completed",
            },
            "database_timings": timings.as_dict(),
        }

    captured = {}

    def fake_get_database_resource_status(*, workload):
        captured["workload"] = workload

        return {
            "connection_strategy": "bounded_pool",
            "pool_topology": "isolated_pools",
            "workload": workload,
            "pool": {
                "name": "background-worker-pool",
            },
        }

    monkeypatch.setattr(
        app_module,
        "process_scheduled_encounter_batch",
        fake_process_scheduled_encounter_batch,
    )
    monkeypatch.setattr(
        app_module,
        "get_database_resource_status",
        fake_get_database_resource_status,
    )

    request = SimpleNamespace(
        state=SimpleNamespace(
            request_id="background-request-001",
        ),
    )

    response = app_module.background_encounter_batch(
        request=request,
        batch_size=2,
        worker_id="test-background-worker",
    )

    assert captured["workload"] == BACKGROUND_WORKLOAD
    assert response["database_resources"]["workload"] == (
        BACKGROUND_WORKLOAD
    )
    assert response["database_resources"]["pool"]["name"] == (
        "background-worker-pool"
    )
