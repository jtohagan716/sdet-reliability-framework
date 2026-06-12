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
def echo():
    latency_ms = random.randint(100, 1200)

    time.sleep(latency_ms / 1000)

    return {
        "message": "echo",
        "timestamp_utc": datetime.now(UTC).isoformat(),
        "simulated_latency_ms": latency_ms,
    }