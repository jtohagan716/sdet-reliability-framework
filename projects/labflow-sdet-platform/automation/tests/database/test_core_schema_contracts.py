import uuid
from datetime import date, datetime, timezone

import psycopg
import pytest
from psycopg import Connection


PATIENT_ID = uuid.UUID(
    "00000000-0000-0000-0000-000000000101"
)
SECOND_PATIENT_ID = uuid.UUID(
    "00000000-0000-0000-0000-000000000102"
)
ENCOUNTER_ID = uuid.UUID(
    "00000000-0000-0000-0000-000000000201"
)
UNKNOWN_PATIENT_ID = uuid.UUID(
    "00000000-0000-0000-0000-000000000999"
)

SYNTHETIC_PATIENT_ID = "SYN-CORE-CONTRACT-001"

pytestmark = [
    pytest.mark.database,
    pytest.mark.regression,
]


def _insert_patient(
    connection: Connection,
    *,
    patient_id: uuid.UUID = PATIENT_ID,
    synthetic_patient_id: str = SYNTHETIC_PATIENT_ID,
    sex: str = "FEMALE",
) -> None:
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
            "Avery",
            "Morgan",
            date(1985, 4, 12),
            sex,
        ),
    )


def _insert_encounter(
    connection: Connection,
    *,
    encounter_id: uuid.UUID = ENCOUNTER_ID,
    patient_id: uuid.UUID = PATIENT_ID,
    encounter_number: str = "ENC-CORE-CONTRACT-001",
    status: str = "OPEN",
    admitted_at: datetime | None = None,
    discharged_at: datetime | None = None,
) -> None:
    admission_time = admitted_at or datetime(
        2026,
        7,
        16,
        13,
        0,
        tzinfo=timezone.utc,
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
            admitted_at,
            discharged_at
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            encounter_id,
            encounter_number,
            patient_id,
            "OUTPATIENT",
            "FAC-TEST-001",
            status,
            admission_time,
            discharged_at,
        ),
    )


def test_patient_and_encounter_relationship_can_be_created(
    db_connection: Connection,
) -> None:
    _insert_patient(db_connection)
    _insert_encounter(db_connection)

    row = db_connection.execute(
        """
        SELECT
            patient.synthetic_patient_id,
            encounter.encounter_number,
            encounter.status
        FROM core.encounters AS encounter
        JOIN core.patients AS patient
          ON patient.id = encounter.patient_id
        WHERE encounter.id = %s
        """,
        (ENCOUNTER_ID,),
    ).fetchone()

    assert row == (
        SYNTHETIC_PATIENT_ID,
        "ENC-CORE-CONTRACT-001",
        "OPEN",
    )


@pytest.mark.negative
def test_encounter_rejects_unknown_patient(
    db_connection: Connection,
) -> None:
    with pytest.raises(
        psycopg.errors.ForeignKeyViolation
    ) as error:
        _insert_encounter(
            db_connection,
            patient_id=UNKNOWN_PATIENT_ID,
        )

    assert (
        error.value.diag.constraint_name
        == "fk_core_encounters_patient_id"
    )


@pytest.mark.negative
def test_patient_rejects_duplicate_synthetic_identifier(
    db_connection: Connection,
) -> None:
    _insert_patient(db_connection)

    with pytest.raises(
        psycopg.errors.UniqueViolation
    ) as error:
        _insert_patient(
            db_connection,
            patient_id=SECOND_PATIENT_ID,
        )

    assert (
        error.value.diag.constraint_name
        == "uq_core_patients_synthetic_patient_id"
    )


@pytest.mark.negative
def test_patient_rejects_unsupported_sex_value(
    db_connection: Connection,
) -> None:
    with pytest.raises(
        psycopg.errors.CheckViolation
    ) as error:
        _insert_patient(
            db_connection,
            sex="UNSUPPORTED",
        )

    assert (
        error.value.diag.constraint_name
        == "ck_core_patients_sex"
    )


@pytest.mark.negative
def test_encounter_rejects_discharge_before_admission(
    db_connection: Connection,
) -> None:
    _insert_patient(db_connection)

    admitted_at = datetime(
        2026,
        7,
        16,
        13,
        0,
        tzinfo=timezone.utc,
    )
    discharged_at = datetime(
        2026,
        7,
        16,
        12,
        59,
        tzinfo=timezone.utc,
    )

    with pytest.raises(
        psycopg.errors.CheckViolation
    ) as error:
        _insert_encounter(
            db_connection,
            admitted_at=admitted_at,
            discharged_at=discharged_at,
        )

    assert (
        error.value.diag.constraint_name
        == "ck_core_encounters_discharge_after_admit"
    )