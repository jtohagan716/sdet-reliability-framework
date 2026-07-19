import logging

from fastapi import FastAPI

from system_under_test.api.config import get_settings
from system_under_test.api.routes.health import router as health_router
from system_under_test.api.routes.orders import router as orders_router

settings = get_settings()

logging.basicConfig(
    level=settings.log_level.upper(),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)

app = FastAPI(
    title="LabFlow System Under Test",
    version="0.1.0",
    description=(
        "Synthetic laboratory-order workflow for SDET and reliability training. "
        "Never use real patient data."
    ),
)

app.include_router(health_router)
app.include_router(orders_router)


@app.get("/")
def root() -> dict[str, str]:
    return {
        "service": "labflow-api",
        "version": "0.1.0",
        "documentation": "/docs",
    }
