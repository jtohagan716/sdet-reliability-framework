import enum
import uuid
from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from system_under_test.api.database import Base


class OrderPriority(str, enum.Enum):
    ROUTINE = "ROUTINE"
    STAT = "STAT"


class LabOrderStatus(str, enum.Enum):
    PLACED = "PLACED"


class Patient(Base):
    __tablename__ = "patients"
    __table_args__ = (
        CheckConstraint(
            "sex IN ('FEMALE', 'MALE', 'OTHER', 'UNKNOWN')",
            name="ck_core_patients_sex",
        ),
        {
            "schema": "core",
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    synthetic_patient_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    first_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    last_name: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    date_of_birth: Mapped[date] = mapped_column(
        Date(),
        nullable=False,
    )
    sex: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class Encounter(Base):
    __tablename__ = "encounters"
    __table_args__ = (
        CheckConstraint(
            (
                "encounter_type IN "
                "('OUTPATIENT', 'INPATIENT', 'EMERGENCY')"
            ),
            name="ck_core_encounters_type",
        ),
        CheckConstraint(
            "status IN ('OPEN', 'CLOSED', 'CANCELLED')",
            name="ck_core_encounters_status",
        ),
        CheckConstraint(
            (
                "discharged_at IS NULL "
                "OR discharged_at >= admitted_at"
            ),
            name="ck_core_encounters_discharge_after_admit",
        ),
        {
            "schema": "core",
        },
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    encounter_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    patient_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey(
            "core.patients.id",
            ondelete="RESTRICT",
        ),
        nullable=False,
        index=True,
    )
    encounter_type: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    facility_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="OPEN",
        index=True,
    )
    admitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    discharged_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )


class LabOrder(Base):
    __tablename__ = "lab_orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    placer_order_number: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
    )
    synthetic_patient_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )
    test_code: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        index=True,
    )
    priority: Mapped[OrderPriority] = mapped_column(
        Enum(OrderPriority, name="order_priority"),
        nullable=False,
        default=OrderPriority.ROUTINE,
    )
    status: Mapped[LabOrderStatus] = mapped_column(
        Enum(LabOrderStatus, name="lab_order_status"),
        nullable=False,
        default=LabOrderStatus.PLACED,
    )
    ordered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )