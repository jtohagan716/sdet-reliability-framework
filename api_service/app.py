import logging
import os
import random
import time
import uuid
import hashlib
import json
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from fastapi.responses import HTMLResponse
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Header, HTTPException, Path, Request
from fastapi.responses import Response
from pydantic import BaseModel
from framework.security.jwt_decoder import decode_jwt
from framework.security.jwt_inspector import inspect_jwt
from api_service.database import (
    close_database_resources,
    get_connection,
    get_database_resource_status,
    initialize_database_resources,
)
from api_service.repositories.patients import get_patient_summary_from_postgres
from api_service.repositories.data_quality_reviews import (
    VALID_REVIEW_STATUSES,
    get_review_item_detail,
    list_review_items,
)
from api_service.database_timings import DatabasePhaseTimings


TRUSTED_ISSUER = "https://company-login.com"
REQUIRED_ROLE = "provider"

HTTP_REQUESTS_TOTAL = Counter(
    "sdet_http_requests_total",
    "Total HTTP requests by method, path, and status code",
    ["method", "path", "status_code"],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "sdet_http_request_duration_seconds",
    "HTTP request duration in seconds by method, path, and status code",
    ["method", "path", "status_code"],
)

PATIENT_DATA_SOURCE = os.getenv("PATIENT_DATA_SOURCE", "memory").lower()
PATIENT_LOOKUP_DEFECT_MODE = os.getenv("PATIENT_LOOKUP_DEFECT_MODE", "none").lower()

PATIENT_LOOKUP_TOTAL = Counter(
    "sdet_patient_lookup_total",
    "Synthetic patient lookup outcomes",
    ["outcome"],
)


@asynccontextmanager
async def lifespan(_: FastAPI):
    initialize_database_resources()

    try:
        yield
    finally:
        close_database_resources()


app = FastAPI(
    title="Synthetic Echo Service",
    description="Controlled test service for reliability and latency simulation.",
    lifespan=lifespan,
)

if os.getenv("OTEL_ENABLED", "false").lower() == "true":
    from api_service.observability.otel_config import configure_opentelemetry

    configure_opentelemetry(app)

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()

logging.basicConfig(
    level=LOG_LEVEL,
    format="%(asctime)s level=%(levelname)s logger=%(name)s message=%(message)s",
)

logger = logging.getLogger("sdet_reliability_api")

def get_metric_path(request: Request) -> str:
    route = request.scope.get("route")
    route_path = getattr(route, "path", None)

    if route_path:
        return route_path

    return request.url.path


def get_or_create_request_id(request: Request) -> str:
    incoming_request_id = request.headers.get("X-Request-ID")

    if incoming_request_id:
        return incoming_request_id[:128]

    return str(uuid.uuid4())

@app.middleware("http")
async def log_request_timing(request: Request, call_next):
    start_time = time.perf_counter()
    request_id = get_or_create_request_id(request)
    request.state.request_id = request_id

    logger.info(
        "request_start request_id=%s method=%s path=%s",
        request_id,
        request.method,
        request.url.path,
    )

    try:
        response = await call_next(request)
    except Exception:
        duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
        duration_seconds = duration_ms / 1000
        metric_path = get_metric_path(request)

        HTTP_REQUESTS_TOTAL.labels(
            method=request.method,
            path=metric_path,
            status_code="500",
        ).inc()

        HTTP_REQUEST_DURATION_SECONDS.labels(
            method=request.method,
            path=metric_path,
            status_code="500",
        ).observe(duration_seconds)

        logger.exception(
            "request_failed request_id=%s method=%s path=%s duration_ms=%s",
            request_id,
            request.method,
            request.url.path,
            duration_ms,
        )
        raise

    duration_ms = round((time.perf_counter() - start_time) * 1000, 2)
    duration_seconds = duration_ms / 1000
    metric_path = get_metric_path(request)
    status_code = str(response.status_code)

    HTTP_REQUESTS_TOTAL.labels(
        method=request.method,
        path=metric_path,
        status_code=status_code,
    ).inc()

    HTTP_REQUEST_DURATION_SECONDS.labels(
        method=request.method,
        path=metric_path,
        status_code=status_code,
    ).observe(duration_seconds)

    response.headers["X-Request-ID"] = request_id

    logger.info(
        "request_complete request_id=%s method=%s path=%s status_code=%s duration_ms=%s",
        request_id,
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )

    return response



class PatientSummary(BaseModel):
    patient_id: int
    name: str
    status: str
    last_visit: str


SYNTHETIC_PATIENTS = {
    1001: {
        "patient_id": 1001,
        "name": "Alex Morgan",
        "status": "active",
        "last_visit": "2026-06-15",
    },
    1002: {
        "patient_id": 1002,
        "name": "Jordan Lee",
        "status": "inactive",
        "last_visit": "2026-05-20",
    },
}

@app.get("/health")
def health():
    return {
        "status": "UP",
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }

@app.get("/metrics")
def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST,
    )


@app.get("/echo")
def echo(mode: str = "normal"):

    if mode == "normal":
        latency_ms = random.randint(100, 500)

    elif mode == "slow":
        latency_ms = random.randint(1000, 2000)

    elif mode == "degraded":
        latency_ms = random.randint(2500, 4000)

    elif mode == "fail":
        return {
            "message": "service_failure",
            "status": "ERROR",
        }

    else:
        latency_ms = 500

    time.sleep(latency_ms / 1000)

    return {
        "message": "echo",
        "mode": mode,
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "simulated_latency_ms": latency_ms,
    }


@app.get("/secure/patient-summary")
def secure_patient_summary(
    authorization: str | None = Header(default=None),
):
    if authorization is None:
        raise HTTPException(
            status_code=401,
            detail="MISSING_AUTHORIZATION_HEADER",
        )

    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="INVALID_AUTHORIZATION_HEADER",
        )

    token = authorization.replace("Bearer ", "")

    try:
        decoded_token = decode_jwt(token)
    except Exception:
        raise HTTPException(
            status_code=401,
            detail="INVALID_TOKEN",
        )

    security_result = inspect_jwt(
        decoded_token,
        required_role=REQUIRED_ROLE,
        trusted_issuer=TRUSTED_ISSUER,
    )

    if security_result["reason"] in [
        "TOKEN_EXPIRED",
        "UNTRUSTED_ISSUER",
    ]:
        raise HTTPException(
            status_code=401,
            detail=security_result["reason"],
        )

    if security_result["reason"] == "ROLE_NOT_AUTHORIZED":
        raise HTTPException(
            status_code=403,
            detail=security_result["reason"],
        )

    return {
        "status": "ACCESS_GRANTED",
        "resource": "patient-summary",
        "subject": security_result["subject"],
        "role": security_result["role"],
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }

@app.get("/patient-lookup", response_class=HTMLResponse)
def patient_lookup_page() -> str:
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <title>Patient Lookup</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
</head>
<body>
    <main>
        <h1>Patient Lookup</h1>

        <p id="lookup-instructions">
            Enter a synthetic patient ID to validate patient lookup behavior.
        </p>

        <form aria-describedby="lookup-instructions">
            <label for="patient-id">Patient ID</label>
            <input
                id="patient-id"
                name="patient-id"
                type="text"
                inputmode="numeric"
                autocomplete="off"
            >

            <button type="submit">Lookup Patient</button>
        </form>

        <section
            aria-live="polite"
            aria-label="Lookup result"
            id="lookup-result"
        >
            No lookup has been submitted.
        </section>
    </main>

    <script>
        const form = document.querySelector("form");
        const input = document.querySelector("#patient-id");
        const result = document.querySelector("#lookup-result");

        form.addEventListener("submit", async (event) => {
            event.preventDefault();

            const patientId = input.value.trim();

            if (!patientId) {
                result.textContent = "Enter a patient ID before submitting.";
                return;
            }

            try {
                const response = await fetch(`/patients/${patientId}`);

                if (response.ok) {
                    const data = await response.json();
                    result.textContent = `Patient lookup succeeded for ${data.patient_id}.`;
                    return;
                }

                result.textContent = `Patient lookup returned status ${response.status}.`;
            } catch (error) {
                result.textContent = "Patient lookup failed because the API could not be reached.";
            }
        });
    </script>
</body>
</html>
"""

@app.post("/qa/idempotency-validation")
async def validate_idempotency_behavior(
    request: Request,
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key",
    ),
):
    """
    Validate retry-safe idempotency behavior.

    Behavior:
    - First request with a new Idempotency-Key stores a response.
    - Retry with the same key and same request body returns the stored response.
    - Retry with the same key but different request body returns a conflict.
    """

    if os.getenv("ENABLE_QA_ENDPOINTS", "false").lower() != "true":
        raise HTTPException(
            status_code=404,
            detail="QA endpoints are disabled",
        )

    if not idempotency_key:
        raise HTTPException(
            status_code=400,
            detail="Idempotency-Key header is required",
        )

    body_bytes = await request.body()

    if body_bytes:
        try:
            request_payload = json.loads(body_bytes)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=400,
                detail="Request body must be valid JSON",
            ) from exc
    else:
        request_payload = {}

    canonical_request = json.dumps(
        request_payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    request_hash = (
        "sha256:"
        + hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
    )

    request_method = request.method
    request_path = request.url.path
    service_name = os.getenv("OTEL_SERVICE_NAME", "sdet-reliability-api")

    synthetic_result_id = hashlib.sha256(
        f"{idempotency_key}:{request_hash}".encode("utf-8")
    ).hexdigest()[:12]

    stored_response_body = {
        "synthetic_operation": "create_encounter",
        "synthetic_result_id": synthetic_result_id,
        "status": "created",
    }

    with get_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    idempotency_key,
                    request_method,
                    request_path,
                    request_hash,
                    response_status,
                    response_body,
                    replayed_count
                FROM idempotency_keys
                WHERE idempotency_key = %s
                FOR UPDATE;
                """,
                (idempotency_key,),
            )

            existing_row = cursor.fetchone()

            if existing_row:
                existing_key = existing_row["idempotency_key"]
                existing_method = existing_row["request_method"]
                existing_path = existing_row["request_path"]
                existing_hash = existing_row["request_hash"]
                existing_status = existing_row["response_status"]
                existing_response_body = existing_row["response_body"]
                existing_replayed_count = existing_row["replayed_count"]

                if (
                    existing_method != request_method
                    or existing_path != request_path
                    or existing_hash != request_hash
                ):
                    connection.rollback()

                    raise HTTPException(
                        status_code=409,
                        detail={
                            "validation": "idempotency_conflict",
                            "message": (
                                "The same Idempotency-Key was reused "
                                "with a different request method, path, or body."
                            ),
                            "idempotency_key": existing_key,
                            "stored_request_hash": existing_hash,
                            "incoming_request_hash": request_hash,
                            "stored_request_method": existing_method,
                            "incoming_request_method": request_method,
                            "stored_request_path": existing_path,
                            "incoming_request_path": request_path,
                        },
                    )

                cursor.execute(
                    """
                    UPDATE idempotency_keys
                    SET
                        replayed_count = replayed_count + 1,
                        last_replayed_at = NOW()
                    WHERE idempotency_key = %s
                    RETURNING replayed_count;
                    """,
                    (idempotency_key,),
                )

                replayed_count = cursor.fetchone()["replayed_count"]
                connection.commit()

                return {
                    "validation": "idempotency_replayed",
                    "idempotency_key": existing_key,
                    "request_hash": existing_hash,
                    "response_status": existing_status,
                    "response_body": existing_response_body,
                    "replayed": True,
                    "replayed_count": replayed_count,
                }

            cursor.execute(
                """
                INSERT INTO idempotency_keys (
                    idempotency_key,
                    request_method,
                    request_path,
                    request_hash,
                    response_status,
                    response_body,
                    service_name
                )
                VALUES (
                    %s,
                    %s,
                    %s,
                    %s,
                    %s,
                    %s::jsonb,
                    %s
                )
                RETURNING
                    idempotency_key,
                    request_hash,
                    response_status,
                    response_body,
                    replayed_count;
                """,
                (
                    idempotency_key,
                    request_method,
                    request_path,
                    request_hash,
                    201,
                    json.dumps(stored_response_body),
                    service_name,
                ),
            )

            created_row = cursor.fetchone()

            created_key = created_row["idempotency_key"]
            created_hash = created_row["request_hash"]
            response_status = created_row["response_status"]
            response_body = created_row["response_body"]
            replayed_count = created_row["replayed_count"]

            connection.commit()

            return {
                "validation": "idempotency_created",
                "idempotency_key": created_key,
                "request_hash": created_hash,
                "response_status": response_status,
                "response_body": response_body,
                "replayed": False,
                "replayed_count": replayed_count,
            }
@app.get("/qa/database-connection-timing")
def database_connection_timing(
    patient_id: int = 1001,
    connection_hold_ms: int = 0,
):
    if os.getenv("ENABLE_QA_ENDPOINTS", "false").lower() != "true":
        raise HTTPException(
            status_code=404,
            detail="QA endpoints are disabled",
        )

    if not 0 <= connection_hold_ms <= 1000:
        raise HTTPException(
            status_code=422,
            detail=(
                "connection_hold_ms must be between "
                "0 and 1000 milliseconds"
            ),
        )

    timings = DatabasePhaseTimings()

    patient = get_patient_summary_from_postgres(
        patient_id,
        defect_mode=PATIENT_LOOKUP_DEFECT_MODE,
        timings=timings,
        connection_hold_ms=connection_hold_ms,
    )

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="PATIENT_NOT_FOUND",
        )

    resource_status = get_database_resource_status()

    return {
        "patient_id": patient_id,
        "connection_hold_ms": connection_hold_ms,
        "connection_strategy": resource_status[
            "connection_strategy"
        ],
        "database_phases": timings.as_dict(),
        "database_resources": resource_status,
    }

@app.get(
    "/patients/{patient_id}",
    response_model=PatientSummary,
    tags=["Synthetic Patient API"],
)
def get_patient_summary(
    request: Request,
    patient_id: int = Path(
        ...,
        description="Synthetic patient identifier used for API validation examples",
    )
):
    request_id = request.state.request_id
    """
    Return a synthetic patient summary for REST API testing.

    This endpoint uses fictional test data only. It does not return PHI,
    production records, credentials, secrets, or real patient information.
    """
    logger.info(
        "patient_lookup_started request_id=%s patient_id=%s data_source=%s defect_mode=%s",
        request_id,
        patient_id,
        PATIENT_DATA_SOURCE,
        PATIENT_LOOKUP_DEFECT_MODE,
    )

    try:
        if PATIENT_DATA_SOURCE == "postgres":
            patient = get_patient_summary_from_postgres(
                patient_id,
                defect_mode=PATIENT_LOOKUP_DEFECT_MODE,
            )
        else:
            patient = SYNTHETIC_PATIENTS.get(patient_id)
    except Exception:
        PATIENT_LOOKUP_TOTAL.labels(outcome="data_source_error").inc()

        logger.exception(
            "patient_lookup_data_source_error request_id=%s patient_id=%s data_source=%s",
            request_id,
            patient_id,
            PATIENT_DATA_SOURCE,
        )

        raise HTTPException(
            status_code=503,
            detail="PATIENT_DATA_SOURCE_UNAVAILABLE",
        )

    if patient is None:
        PATIENT_LOOKUP_TOTAL.labels(outcome="not_found").inc()

        logger.warning(
            "patient_lookup_not_found request_id=%s patient_id=%s",
            request_id,
            patient_id,
        )

        raise HTTPException(
            status_code=404,
            detail=f"Synthetic patient {patient_id} not found",
        )

    PATIENT_LOOKUP_TOTAL.labels(outcome="success").inc()

    logger.info(
        "patient_lookup_success request_id=%s patient_id=%s status=%s",
        request_id,
        patient_id,
        patient["status"],
    )

    return patient

@app.post("/qa/audit-otel-validation")
def audit_otel_validation(request: Request):
    """
    Local validation endpoint for audit + OpenTelemetry trace correlation.

    This endpoint:
    - creates a synthetic encounter
    - updates the encounter status
    - allows the PostgreSQL audit trigger to write audit rows
    - stores the active OpenTelemetry trace_id/span_id in encounter_audit
    """

    if os.getenv("ENABLE_QA_ENDPOINTS", "false").lower() != "true":
        raise HTTPException(
            status_code=404,
            detail="QA endpoint is not enabled",
        )
    from api_service.observability.audit_context import set_postgres_audit_context
    with get_connection() as connection:
        trace_id, span_id = set_postgres_audit_context(
            connection=connection,
            request=request,
        )

        refs = connection.execute(
            """
            SELECT
                COALESCE((SELECT MAX(encounter_id) FROM encounters), 0) + 1 AS encounter_id,
                (SELECT MIN(patient_id) FROM patients) AS patient_id,
                (SELECT MIN(provider_id) FROM providers) AS provider_id,
                (SELECT MIN(facility_id) FROM facilities) AS facility_id
            """
        ).fetchone()

        encounter_id = refs["encounter_id"]

        connection.execute(
            """
            INSERT INTO encounters (
                encounter_id,
                patient_id,
                provider_id,
                facility_id,
                encounter_date,
                encounter_type,
                status
            )
            VALUES (
                %s,
                %s,
                %s,
                %s,
                CURRENT_DATE,
                'primary_care',
                'scheduled'
            )
            """,
            (
                encounter_id,
                refs["patient_id"],
                refs["provider_id"],
                refs["facility_id"],
            ),
        )

        connection.execute(
            """
            UPDATE encounters
            SET status = 'completed'
            WHERE encounter_id = %s
            """,
            (encounter_id,),
        )

        connection.commit()

        audit_rows = connection.execute(
            """
            SELECT
                audit_id,
                encounter_id,
                operation_type,
                old_status,
                new_status,
                trace_id,
                span_id,
                request_id,
                request_method,
                request_path,
                service_name,
                changed_at
            FROM encounter_audit
            WHERE encounter_id = %s
            ORDER BY audit_id
            """,
            (encounter_id,),
        ).fetchall()

    return {
        "validation": "passed" if len(audit_rows) == 2 else "review_required",
        "encounter_id": encounter_id,
        "trace_id": trace_id,
        "span_id": span_id,
        "audit_row_count": len(audit_rows),
        "audit_rows": audit_rows,
    }

@app.get("/qa/data-quality-review-items")
def get_patient_data_quality_review_items(
    review_status: str | None = None,
    limit: int = 25,
):
    if review_status is not None and review_status not in VALID_REVIEW_STATUSES:
        raise HTTPException(status_code=400, detail="INVALID_REVIEW_STATUS")

    try:
        review_items = list_review_items(
            review_status=review_status,
            limit=limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="PATIENT_DATA_QUALITY_REVIEW_QUEUE_UNAVAILABLE",
        ) from exc

    return {
        "review_items": review_items,
        "count": len(review_items),
    }

@app.get("/qa/data-quality-review-items/{review_item_key}")
def get_patient_data_quality_review_item(review_item_key: str):
    try:
        review_item = get_review_item_detail(review_item_key)
    except Exception as exc:
        raise HTTPException(
            status_code=503,
            detail="PATIENT_DATA_QUALITY_REVIEW_QUEUE_UNAVAILABLE",
        ) from exc

    if review_item is None:
        raise HTTPException(status_code=404, detail="REVIEW_ITEM_NOT_FOUND")

    return review_item
