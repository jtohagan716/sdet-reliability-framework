import enum
import uuid
from datetime import datetime

from sqlalchemy import DateTime, Enum, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from system_under_test.api.database import Base


class OrderPriority(str, enum.Enum):
    ROUTINE = "ROUTINE"
    STAT = "STAT"


class LabOrderStatus(str, enum.Enum):
    PLACED = "PLACED"


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
