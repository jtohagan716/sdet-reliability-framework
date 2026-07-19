from typing import Sequence

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    order_priority = postgresql.ENUM(
        "ROUTINE",
        "STAT",
        name="order_priority",
        create_type=True,
    )
    lab_order_status = postgresql.ENUM(
        "PLACED",
        name="lab_order_status",
        create_type=True,
    )

    op.create_table(
        "lab_orders",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("placer_order_number", sa.String(length=50), nullable=False),
        sa.Column("synthetic_patient_id", sa.String(length=50), nullable=False),
        sa.Column("test_code", sa.String(length=30), nullable=False),
        sa.Column("priority", order_priority, nullable=False),
        sa.Column("status", lab_order_status, nullable=False),
        sa.Column("ordered_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "placer_order_number",
            name="uq_lab_orders_placer_order_number",
        ),
    )
    op.create_index(
        "ix_lab_orders_synthetic_patient_id",
        "lab_orders",
        ["synthetic_patient_id"],
        unique=False,
    )
    op.create_index(
        "ix_lab_orders_test_code",
        "lab_orders",
        ["test_code"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_lab_orders_test_code", table_name="lab_orders")
    op.drop_index("ix_lab_orders_synthetic_patient_id", table_name="lab_orders")
    op.drop_table("lab_orders")
    postgresql.ENUM(name="lab_order_status").drop(
        op.get_bind(),
        checkfirst=True,
    )
    postgresql.ENUM(name="order_priority").drop(
        op.get_bind(),
        checkfirst=True,
    )
