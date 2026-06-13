import random
import time
from datetime import datetime, UTC

from fastapi import FastAPI


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