"""
Helpers for connecting application context to PostgreSQL audit rows.
"""

import os
from typing import Optional

import psycopg
from fastapi import Request
from opentelemetry import trace


def get_current_trace_ids() -> tuple[Optional[str], Optional[str]]:
    """
    Return the active OpenTelemetry trace_id and span_id as lowercase hex strings.

    trace_id: 32 hex characters
    span_id: 16 hex characters
    """

    current_span = trace.get_current_span()
    span_context = current_span.get_span_context()

    if not span_context or not span_context.is_valid:
        return None, None

    trace_id = f"{span_context.trace_id:032x}"
    span_id = f"{span_context.span_id:016x}"

    return trace_id, span_id


def set_postgres_audit_values(
    connection: psycopg.Connection,
    *,
    trace_id: Optional[str] = None,
    span_id: Optional[str] = None,
    request_id: str = "",
    request_method: str = "",
    request_path: str = "",
    service_name: str = "",
    changed_by: str = "",
    change_source: str = "",
) -> None:
    """
    Store audit and correlation values in PostgreSQL transaction-local settings.

    The encounter audit trigger reads these values with current_setting(...)
    and writes them into encounter_audit.

    This generic helper can be used by HTTP requests and background workers.
    It must be called before audited INSERT, UPDATE, or DELETE statements.
    """

    resolved_service_name = (
        service_name
        or os.getenv(
            "OTEL_SERVICE_NAME",
            "sdet-reliability-api",
        )
    )

    connection.execute(
        """
        SELECT
            set_config('app.trace_id', %s, true),
            set_config('app.span_id', %s, true),
            set_config('app.request_id', %s, true),
            set_config('app.request_method', %s, true),
            set_config('app.request_path', %s, true),
            set_config('app.service_name', %s, true),
            set_config('app.changed_by', %s, true),
            set_config('app.change_source', %s, true)
        """,
        (
            trace_id or "",
            span_id or "",
            request_id or "",
            request_method or "",
            request_path or "",
            resolved_service_name,
            changed_by or "",
            change_source or "",
        ),
    )


def set_postgres_audit_context(
    connection: psycopg.Connection,
    request: Request,
) -> tuple[Optional[str], Optional[str]]:
    """
    Store HTTP request and trace context in PostgreSQL transaction-local settings.
    """

    trace_id, span_id = get_current_trace_ids()

    request_id = getattr(request.state, "request_id", "")

    set_postgres_audit_values(
        connection,
        trace_id=trace_id,
        span_id=span_id,
        request_id=request_id,
        request_method=request.method,
        request_path=request.url.path,
        changed_by="sdet-reliability-api",
        change_source="http_request",
    )

    return trace_id, span_id
