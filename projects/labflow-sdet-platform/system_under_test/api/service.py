import uuid

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError

from system_under_test.api.models import LabOrder
from system_under_test.api.repository import LabOrderRepository
from system_under_test.api.schemas import LabOrderCreate


class LabOrderService:
    def __init__(self, repository: LabOrderRepository) -> None:
        self._repository = repository

    def create_order(self, request: LabOrderCreate) -> LabOrder:
        existing = self._repository.get_by_placer_order_number(
            request.placer_order_number
        )
        if existing is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="placer_order_number already exists",
            )

        try:
            return self._repository.create(request)
        except IntegrityError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="laboratory order conflicts with existing data",
            ) from exc

    def get_order(self, order_id: uuid.UUID) -> LabOrder:
        order = self._repository.get_by_id(order_id)
        if order is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="laboratory order not found",
            )
        return order

    def list_orders(self, limit: int, offset: int) -> list[LabOrder]:
        return self._repository.list_orders(limit=limit, offset=offset)
