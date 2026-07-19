import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from system_under_test.api.database import get_db_session
from system_under_test.api.repository import LabOrderRepository
from system_under_test.api.schemas import LabOrderCreate, LabOrderResponse
from system_under_test.api.service import LabOrderService

router = APIRouter(prefix="/api/v1/lab-orders", tags=["laboratory orders"])


def get_service(
    session: Annotated[Session, Depends(get_db_session)],
) -> LabOrderService:
    return LabOrderService(LabOrderRepository(session))


@router.post(
    "",
    response_model=LabOrderResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_lab_order(
    request: LabOrderCreate,
    service: Annotated[LabOrderService, Depends(get_service)],
) -> LabOrderResponse:
    return LabOrderResponse.model_validate(service.create_order(request))


@router.get("/{order_id}", response_model=LabOrderResponse)
def get_lab_order(
    order_id: uuid.UUID,
    service: Annotated[LabOrderService, Depends(get_service)],
) -> LabOrderResponse:
    return LabOrderResponse.model_validate(service.get_order(order_id))


@router.get("", response_model=list[LabOrderResponse])
def list_lab_orders(
    service: Annotated[LabOrderService, Depends(get_service)],
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> list[LabOrderResponse]:
    return [
        LabOrderResponse.model_validate(order)
        for order in service.list_orders(limit=limit, offset=offset)
    ]
