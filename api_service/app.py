import random
import time
from datetime import datetime, UTC

from fastapi import FastAPI, Header, HTTPException

from framework.security.jwt_decoder import decode_jwt
from framework.security.jwt_inspector import inspect_jwt


TRUSTED_ISSUER = "https://company-login.com"
REQUIRED_ROLE = "provider"


app = FastAPI(
    title="Synthetic Echo Service",
    description="Controlled test service for reliability and latency simulation.",
)


@app.get("/health")
def health():
    return {
        "status": "UP",
        "timestamp_utc": datetime.now(UTC).isoformat(),
    }


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