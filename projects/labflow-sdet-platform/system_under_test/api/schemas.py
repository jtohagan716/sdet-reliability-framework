import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from system_under_test.api.models import LabOrderStatus, OrderPriority


class LabOrderCreate(BaseModel):
    placer_order_number: str = Field(min_length=1, max_length=50)
    synthetic_patient_id: str = Field(
        min_length=1,
        max_length=50,
        description="Synthetic identifier only. Never use real patient data.",
    )
    test_code: str = Field(min_length=1, max_length=30)
    priority: OrderPriority = OrderPriority.ROUTINE
    ordered_at: datetime


class LabOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placer_order_number: str
    synthetic_patient_id: str
    test_code: str
    priority: OrderPriority
    status: LabOrderStatus
    ordered_at: datetime
    created_at: datetime
