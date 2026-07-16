import uuid
from datetime import datetime
from typing import Self

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    model_validator,
)

from system_under_test.api.models import (
    LabOrderStatus,
    OrderPriority,
)


class LabOrderCreate(BaseModel):
    placer_order_number: str = Field(
        min_length=1,
        max_length=50,
    )
    synthetic_patient_id: str = Field(
        min_length=1,
        max_length=50,
        description=(
            "Synthetic identifier only. Never use real patient data."
        ),
    )
    patient_id: uuid.UUID | None = None
    encounter_id: uuid.UUID | None = None
    test_code: str = Field(
        min_length=1,
        max_length=30,
    )
    priority: OrderPriority = OrderPriority.ROUTINE
    ordered_at: datetime

    @model_validator(mode="after")
    def validate_clinical_context_pair(self) -> Self:
        patient_missing = self.patient_id is None
        encounter_missing = self.encounter_id is None

        if patient_missing != encounter_missing:
            raise ValueError(
                "patient_id and encounter_id must be provided together"
            )

        return self


class LabOrderResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    placer_order_number: str
    synthetic_patient_id: str
    patient_id: uuid.UUID | None = None
    encounter_id: uuid.UUID | None = None
    test_code: str
    priority: OrderPriority
    status: LabOrderStatus
    ordered_at: datetime
    created_at: datetime
