from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "0003"
down_revision: str | None = "0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_core_encounters_id_patient_id",
        "encounters",
        ["id", "patient_id"],
        schema="core",
    )

    op.add_column(
        "lab_orders",
        sa.Column(
            "patient_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )
    op.add_column(
        "lab_orders",
        sa.Column(
            "encounter_id",
            postgresql.UUID(as_uuid=True),
            nullable=True,
        ),
    )

    op.create_check_constraint(
        "ck_lab_orders_clinical_context_pair",
        "lab_orders",
        (
            "(patient_id IS NULL AND encounter_id IS NULL) "
            "OR "
            "(patient_id IS NOT NULL AND encounter_id IS NOT NULL)"
        ),
    )

    op.create_foreign_key(
        "fk_lab_orders_encounter_patient",
        "lab_orders",
        "encounters",
        ["encounter_id", "patient_id"],
        ["id", "patient_id"],
        referent_schema="core",
        ondelete="RESTRICT",
    )

    op.create_index(
        "ix_lab_orders_patient_id",
        "lab_orders",
        ["patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_lab_orders_encounter_id",
        "lab_orders",
        ["encounter_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_lab_orders_encounter_id",
        table_name="lab_orders",
    )
    op.drop_index(
        "ix_lab_orders_patient_id",
        table_name="lab_orders",
    )

    op.drop_constraint(
        "fk_lab_orders_encounter_patient",
        "lab_orders",
        type_="foreignkey",
    )
    op.drop_constraint(
        "ck_lab_orders_clinical_context_pair",
        "lab_orders",
        type_="check",
    )

    op.drop_column("lab_orders", "encounter_id")
    op.drop_column("lab_orders", "patient_id")

    op.drop_constraint(
        "uq_core_encounters_id_patient_id",
        "encounters",
        schema="core",
        type_="unique",
    )