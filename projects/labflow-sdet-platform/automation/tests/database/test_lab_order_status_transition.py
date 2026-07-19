import uuid
from datetime import date, datetime, timezone

import psycopg
import pytest
from psycopg import Connection


def _insert_clinical_context(
    connection: Connection,
) -> dict[str, uuid.UUID | str]:
    patient_id = uuid.uuid4()
    encounter_id = uuid.uuid4()
    unique_suffix = uuid.uuid4().hex[:8]

    synthetic_patient_id = (
        f"SYN-DB-TRANSITION-{unique_suffix}"
    )
    encounter_number = (
        f"ENC-DB-TRANSITION-{unique_suffix}"
    )

    connection.execute(
        """
        INSERT INTO core.patients (
            id,
            synthetic_patient_id,
            first_name,
            last_name,
            date_of_birth,
            sex
        )
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (
            patient_id,
            synthetic_patient_id,
            "Morgan",
            "Reed",
            date(1985, 4, 12),
            "UNKNOWN",
        ),
    )

    connection.execute(
        """
        INSERT INTO core.encounters (
            id,
            encounter_number,
            patient_id,
            encounter_type,
            facility_code,
            status,
            admitted_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            encounter_id,
            encounter_number,
            patient_id,
            "OUTPATIENT",
            "FAC-DB-TRANSITION",
            "OPEN",
            datetime(
                2026,
                7,
                16,
                14,
                0,
                tzinfo=timezone.utc,
            ),
        ),
    )

    return {
        "patient_id": patient_id,
        "encounter_id": encounter_id,
        "synthetic_patient_id": synthetic_patient_id,
        "encounter_number": encounter_number,
    }


def _insert_lab_order(
    connection: Connection,
    clinical_context: dict[str, uuid.UUID | str],
) -> uuid.UUID:
    lab_order_id = uuid.uuid4()
    unique_suffix = uuid.uuid4().hex[:8]

    connection.execute(
        """
        INSERT INTO public.lab_orders (
            id,
            placer_order_number,
            synthetic_patient_id,
            patient_id,
            encounter_id,
            test_code,
            priority,
            status,
            ordered_at,
            created_at
        )
        VALUES (
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            %s,
            NOW(),
            NOW()
        )
        """,
        (
            lab_order_id,
            f"DB-TRANSITION-{unique_suffix}",
            clinical_context["synthetic_patient_id"],
            clinical_context["patient_id"],
            clinical_context["encounter_id"],
            "CBC",
            "ROUTINE",
            "PLACED",
        ),
    )

    return lab_order_id


def _transition_lab_order_status(
    connection: Connection,
    lab_order_id: uuid.UUID,
    requested_status: str,
) -> str:
    row = connection.execute(
        """
        SELECT public.transition_lab_order_status(
            %s,
            %s::public.lab_order_status
        )
        """,
        (
            lab_order_id,
            requested_status,
        ),
    ).fetchone()

    assert row is not None

    return row[0]


def _read_lab_order_status(
    connection: Connection,
    lab_order_id: uuid.UUID,
) -> str:
    row = connection.execute(
        """
        SELECT status
        FROM public.lab_orders
        WHERE id = %s
        """,
        (lab_order_id,),
    ).fetchone()

    assert row is not None

    return row[0]


def test_valid_transition_updates_order_and_returns_new_status(
    db_connection: Connection,
) -> None:
    clinical_context = _insert_clinical_context(
        db_connection
    )
    lab_order_id = _insert_lab_order(
        db_connection,
        clinical_context,
    )

    returned_status = _transition_lab_order_status(
        db_connection,
        lab_order_id,
        "IN_PROGRESS",
    )

    stored_status = _read_lab_order_status(
        db_connection,
        lab_order_id,
    )

    assert returned_status == "IN_PROGRESS"
    assert stored_status == "IN_PROGRESS"


@pytest.mark.negative
def test_invalid_transition_is_rejected_without_changing_order(
    db_connection: Connection,
) -> None:
    clinical_context = _insert_clinical_context(
        db_connection
    )
    lab_order_id = _insert_lab_order(
        db_connection,
        clinical_context,
    )

    db_connection.execute(
        "SAVEPOINT invalid_status_transition"
    )

    with pytest.raises(
        psycopg.errors.CheckViolation,
        match="Invalid lab order status transition",
    ):
        _transition_lab_order_status(
            db_connection,
            lab_order_id,
            "COMPLETED",
        )

    db_connection.execute(
        "ROLLBACK TO SAVEPOINT invalid_status_transition"
    )
    db_connection.execute(
        "RELEASE SAVEPOINT invalid_status_transition"
    )

    stored_status = _read_lab_order_status(
        db_connection,
        lab_order_id,
    )

    assert stored_status == "PLACED"


@pytest.mark.negative
def test_transition_rejects_unknown_lab_order(
    db_connection: Connection,
) -> None:
    missing_lab_order_id = uuid.uuid4()

    db_connection.execute(
        "SAVEPOINT missing_lab_order"
    )

    with pytest.raises(
        psycopg.errors.NoDataFound,
        match="Lab order does not exist",
    ):
        _transition_lab_order_status(
            db_connection,
            missing_lab_order_id,
            "IN_PROGRESS",
        )

    db_connection.execute(
        "ROLLBACK TO SAVEPOINT missing_lab_order"
    )
    db_connection.execute(
        "RELEASE SAVEPOINT missing_lab_order"
    )



def _read_status_audit_rows(
    connection: Connection,
    lab_order_id: uuid.UUID,
):
    return connection.execute(
        """
        SELECT
            previous_status,
            new_status,
            changed_by,
            application_name,
            changed_at
        FROM public.lab_order_status_audit
        WHERE lab_order_id = %s
        ORDER BY id
        """,
        (lab_order_id,),
    ).fetchall()


def test_valid_transition_creates_status_audit_record(
    db_connection: Connection,
) -> None:
    clinical_context = _insert_clinical_context(
        db_connection
    )
    lab_order_id = _insert_lab_order(
        db_connection,
        clinical_context,
    )

    expected_database_user = db_connection.execute(
        "SELECT current_user"
    ).fetchone()[0]

    expected_application_name = db_connection.execute(
        """
        SELECT current_setting(
            'application_name'
        )
        """
    ).fetchone()[0]

    _transition_lab_order_status(
        db_connection,
        lab_order_id,
        "IN_PROGRESS",
    )

    audit_rows = _read_status_audit_rows(
        db_connection,
        lab_order_id,
    )

    assert len(audit_rows) == 1

    (
        previous_status,
        new_status,
        changed_by,
        application_name,
        changed_at,
    ) = audit_rows[0]

    assert previous_status == "PLACED"
    assert new_status == "IN_PROGRESS"
    assert changed_by == expected_database_user
    assert application_name == expected_application_name
    assert changed_at is not None


@pytest.mark.negative
def test_rejected_transition_creates_no_status_audit_record(
    db_connection: Connection,
) -> None:
    clinical_context = _insert_clinical_context(
        db_connection
    )
    lab_order_id = _insert_lab_order(
        db_connection,
        clinical_context,
    )

    db_connection.execute(
        "SAVEPOINT rejected_audit_transition"
    )

    with pytest.raises(
        psycopg.errors.CheckViolation,
        match="Invalid lab order status transition",
    ):
        _transition_lab_order_status(
            db_connection,
            lab_order_id,
            "COMPLETED",
        )

    db_connection.execute(
        "ROLLBACK TO SAVEPOINT rejected_audit_transition"
    )
    db_connection.execute(
        "RELEASE SAVEPOINT rejected_audit_transition"
    )

    audit_rows = _read_status_audit_rows(
        db_connection,
        lab_order_id,
    )

    assert audit_rows == []


def test_unchanged_status_assignment_creates_no_audit_record(
    db_connection: Connection,
) -> None:
    clinical_context = _insert_clinical_context(
        db_connection
    )
    lab_order_id = _insert_lab_order(
        db_connection,
        clinical_context,
    )

    db_connection.execute(
        """
        UPDATE public.lab_orders
        SET status = status
        WHERE id = %s
        """,
        (lab_order_id,),
    )

    audit_rows = _read_status_audit_rows(
        db_connection,
        lab_order_id,
    )

    assert audit_rows == []



def test_status_and_audit_record_roll_back_together(
    db_connection: Connection,
) -> None:
    clinical_context = _insert_clinical_context(
        db_connection
    )
    lab_order_id = _insert_lab_order(
        db_connection,
        clinical_context,
    )

    db_connection.execute(
        "SAVEPOINT status_audit_atomicity"
    )

    returned_status = _transition_lab_order_status(
        db_connection,
        lab_order_id,
        "IN_PROGRESS",
    )

    assert returned_status == "IN_PROGRESS"
    assert (
        _read_lab_order_status(
            db_connection,
            lab_order_id,
        )
        == "IN_PROGRESS"
    )
    assert len(
        _read_status_audit_rows(
            db_connection,
            lab_order_id,
        )
    ) == 1

    db_connection.execute(
        "ROLLBACK TO SAVEPOINT status_audit_atomicity"
    )
    db_connection.execute(
        "RELEASE SAVEPOINT status_audit_atomicity"
    )

    assert (
        _read_lab_order_status(
            db_connection,
            lab_order_id,
        )
        == "PLACED"
    )
    assert (
        _read_status_audit_rows(
            db_connection,
            lab_order_id,
        )
        == []
    )


def test_complete_lifecycle_creates_ordered_audit_history(
    db_connection: Connection,
) -> None:
    clinical_context = _insert_clinical_context(
        db_connection
    )
    lab_order_id = _insert_lab_order(
        db_connection,
        clinical_context,
    )

    first_result = _transition_lab_order_status(
        db_connection,
        lab_order_id,
        "IN_PROGRESS",
    )
    second_result = _transition_lab_order_status(
        db_connection,
        lab_order_id,
        "COMPLETED",
    )

    assert first_result == "IN_PROGRESS"
    assert second_result == "COMPLETED"

    stored_status = _read_lab_order_status(
        db_connection,
        lab_order_id,
    )
    audit_rows = _read_status_audit_rows(
        db_connection,
        lab_order_id,
    )

    assert stored_status == "COMPLETED"
    assert len(audit_rows) == 2

    status_history = [
        (
            row[0],
            row[1],
        )
        for row in audit_rows
    ]

    assert status_history == [
        (
            "PLACED",
            "IN_PROGRESS",
        ),
        (
            "IN_PROGRESS",
            "COMPLETED",
        ),
    ]

    assert audit_rows[0][4] <= audit_rows[1][4]
