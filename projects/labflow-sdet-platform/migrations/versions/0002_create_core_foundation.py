from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE SCHEMA IF NOT EXISTS core")

    op.create_table(
        "patients",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "synthetic_patient_id",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "first_name",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "last_name",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "date_of_birth",
            sa.Date(),
            nullable=False,
        ),
        sa.Column(
            "sex",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            "sex IN ('FEMALE', 'MALE', 'OTHER', 'UNKNOWN')",
            name="ck_core_patients_sex",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_core_patients",
        ),
        sa.UniqueConstraint(
            "synthetic_patient_id",
            name="uq_core_patients_synthetic_patient_id",
        ),
        schema="core",
    )

    op.create_table(
        "encounters",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "encounter_number",
            sa.String(length=50),
            nullable=False,
        ),
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
        ),
        sa.Column(
            "encounter_type",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "facility_code",
            sa.String(length=30),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
        ),
        sa.Column(
            "admitted_at",
            sa.DateTime(timezone=True),
            nullable=False,
        ),
        sa.Column(
            "discharged_at",
            sa.DateTime(timezone=True),
            nullable=True,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.CheckConstraint(
            (
                "encounter_type IN "
                "('OUTPATIENT', 'INPATIENT', 'EMERGENCY')"
            ),
            name="ck_core_encounters_type",
        ),
        sa.CheckConstraint(
            "status IN ('OPEN', 'CLOSED', 'CANCELLED')",
            name="ck_core_encounters_status",
        ),
        sa.CheckConstraint(
            (
                "discharged_at IS NULL "
                "OR discharged_at >= admitted_at"
            ),
            name="ck_core_encounters_discharge_after_admit",
        ),
        sa.ForeignKeyConstraint(
            ["patient_id"],
            ["core.patients.id"],
            name="fk_core_encounters_patient_id",
            ondelete="RESTRICT",
        ),
        sa.PrimaryKeyConstraint(
            "id",
            name="pk_core_encounters",
        ),
        sa.UniqueConstraint(
            "encounter_number",
            name="uq_core_encounters_encounter_number",
        ),
        schema="core",
    )

    op.create_index(
        "ix_core_encounters_patient_id",
        "encounters",
        ["patient_id"],
        unique=False,
        schema="core",
    )

    op.create_index(
        "ix_core_encounters_status",
        "encounters",
        ["status"],
        unique=False,
        schema="core",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_core_encounters_status",
        table_name="encounters",
        schema="core",
    )
    op.drop_index(
        "ix_core_encounters_patient_id",
        table_name="encounters",
        schema="core",
    )

    op.drop_table(
        "encounters",
        schema="core",
    )
    op.drop_table(
        "patients",
        schema="core",
    )

    op.execute("DROP SCHEMA IF EXISTS core")