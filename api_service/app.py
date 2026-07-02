import logging
import os
import random
import time
import uuid
from datetime import datetime, UTC

from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi import FastAPI, Header, HTTPException, Path, Request
from fastapi.responses import Response
from pydantic import BaseModel
from framework.security.jwt_decoder import decode_jwt
from framework.security.jwt_inspector import inspect_jwt


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

PATIENT_LOOKUP_TOTAL = Counter(
    "sdet_patient_lookup_total",
    "Synthetic patient lookup outcomes",
    ["outcome"],
)


app = FastAPI(
    title="Synthetic Echo Service",
    description="Controlled test service for reliability and latency simulation.",
)
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
        "patient_lookup_started request_id=%s patient_id=%s",
        request_id,
        patient_id,
    )

    patient = SYNTHETIC_PATIENTS.get(patient_id)

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
