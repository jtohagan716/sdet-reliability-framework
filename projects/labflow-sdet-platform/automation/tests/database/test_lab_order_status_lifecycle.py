import pytest
from psycopg import Connection


REQUIRED_LAB_ORDER_STATUSES = (
    "PLACED",
    "IN_PROGRESS",
    "COMPLETED",
    "CANCELLED",
)

VALID_TRANSITIONS = (
    ("PLACED", "IN_PROGRESS"),
    ("PLACED", "CANCELLED"),
    ("IN_PROGRESS", "COMPLETED"),
    ("IN_PROGRESS", "CANCELLED"),
)

INVALID_TRANSITIONS = (
    ("PLACED", "PLACED"),
    ("PLACED", "COMPLETED"),
    ("IN_PROGRESS", "PLACED"),
    ("IN_PROGRESS", "IN_PROGRESS"),
    ("COMPLETED", "PLACED"),
    ("COMPLETED", "IN_PROGRESS"),
    ("COMPLETED", "COMPLETED"),
    ("COMPLETED", "CANCELLED"),
    ("CANCELLED", "PLACED"),
    ("CANCELLED", "IN_PROGRESS"),
    ("CANCELLED", "COMPLETED"),
    ("CANCELLED", "CANCELLED"),
)


def _is_valid_transition(
    db_connection: Connection,
    current_status: str,
    requested_status: str,
) -> bool:
    row = db_connection.execute(
        """
        SELECT public.is_valid_lab_order_status_transition(
            %s::public.lab_order_status,
            %s::public.lab_order_status
        )
        """,
        (
            current_status,
            requested_status,
        ),
    ).fetchone()

    assert row is not None

    return row[0]


def test_lab_order_status_enum_contains_required_lifecycle_values(
    db_connection: Connection,
) -> None:
    rows = db_connection.execute(
        """
        SELECT enum_value.enumlabel
        FROM pg_type AS enum_type
        JOIN pg_enum AS enum_value
            ON enum_value.enumtypid = enum_type.oid
        JOIN pg_namespace AS namespace
            ON namespace.oid = enum_type.typnamespace
        WHERE namespace.nspname = 'public'
          AND enum_type.typname = 'lab_order_status'
        ORDER BY enum_value.enumsortorder
        """
    ).fetchall()

    actual_statuses = tuple(row[0] for row in rows)

    assert actual_statuses == REQUIRED_LAB_ORDER_STATUSES


@pytest.mark.parametrize(
    (
        "current_status",
        "requested_status",
    ),
    VALID_TRANSITIONS,
)
def test_valid_lab_order_status_transition_is_accepted(
    db_connection: Connection,
    current_status: str,
    requested_status: str,
) -> None:
    assert _is_valid_transition(
        db_connection,
        current_status,
        requested_status,
    )


@pytest.mark.negative
@pytest.mark.parametrize(
    (
        "current_status",
        "requested_status",
    ),
    INVALID_TRANSITIONS,
)
def test_invalid_lab_order_status_transition_is_rejected(
    db_connection: Connection,
    current_status: str,
    requested_status: str,
) -> None:
    assert not _is_valid_transition(
        db_connection,
        current_status,
        requested_status,
    )
