"""
OpenTelemetry configuration for the SDET Reliability API.

This module wires FastAPI and Psycopg tracing to the OpenTelemetry Collector.
"""

import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg import PsycopgInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def configure_opentelemetry(app: FastAPI) -> None:
    """
    Configure OpenTelemetry tracing for the FastAPI application.

    Captures:
    - inbound FastAPI HTTP request spans
    - Psycopg PostgreSQL client spans
    - export to the OpenTelemetry Collector over OTLP/gRPC
    """

    service_name = os.getenv("OTEL_SERVICE_NAME", "sdet-reliability-api")
    otlp_endpoint = os.getenv(
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "http://otel-collector:4317",
    )

    resource = Resource.create(
        {
            "service.name": service_name,
            "deployment.environment": os.getenv("APP_ENV", "local"),
        }
    )

    tracer_provider = TracerProvider(resource=resource)

    otlp_exporter = OTLPSpanExporter(
        endpoint=otlp_endpoint,
        insecure=True,
    )

    tracer_provider.add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    trace.set_tracer_provider(tracer_provider)

    FastAPIInstrumentor.instrument_app(app)

    PsycopgInstrumentor().instrument()