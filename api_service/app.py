import random
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
from datetime import datetime, UTC
from fastapi import FastAPI, Header, HTTPException, Path
from pydantic import BaseModel
from framework.security.jwt_decoder import decode_jwt
from framework.security.jwt_inspector import inspect_jwt


TRUSTED_ISSUER = "https://company-login.com"
REQUIRED_ROLE = "provider"

REQUEST_COUNT = Counter(
    "sdet_api_request_count",
    "Total number of API requests received",
    ["endpoint"],
)

REQUEST_LATENCY = Histogram(
    "sdet_api_request_latency_seconds",
    "API request latency in seconds",
    ["endpoint"],
)


app = FastAPI(
    title="Synthetic Echo Service",
    description="Controlled test service for reliability and latency simulation.",
)
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
    endpoint = "/health"
    REQUEST_COUNT.labels(endpoint=endpoint).inc()

    with REQUEST_LATENCY.labels(endpoint=endpoint).time():
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
    patient_id: int = Path(
        ...,
        description="Synthetic patient identifier used for API validation examples",
    )
):
    """
    Return a synthetic patient summary for REST API testing.

    This endpoint uses fictional test data only. It does not return PHI,
    production records, credentials, secrets, or real patient information.
    """
    patient = SYNTHETIC_PATIENTS.get(patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail=f"Synthetic patient {patient_id} not found",
        )

    return patient