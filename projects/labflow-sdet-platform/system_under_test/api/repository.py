import uuid

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from system_under_test.api.models import LabOrder
from system_under_test.api.schemas import LabOrderCreate


class LabOrderRepository:
    def __init__(self, session: Session) -> None:
        self._session = session

    def create(self, request: LabOrderCreate) -> LabOrder:
        order = LabOrder(**request.model_dump())
        self._session.add(order)

        try:
            self._session.commit()
        except IntegrityError:
            self._session.rollback()
            raise

        self._session.refresh(order)
        return order

    def get_by_id(
        self,
        order_id: uuid.UUID,
    ) -> LabOrder | None:
        return self._session.get(LabOrder, order_id)

    def get_by_placer_order_number(
        self,
        placer_order_number: str,
    ) -> LabOrder | None:
        statement = select(LabOrder).where(
            LabOrder.placer_order_number
            == placer_order_number
        )
        return self._session.scalar(statement)

    def list_orders(
        self,
        limit: int,
        offset: int,
    ) -> list[LabOrder]:
        statement = (
            select(LabOrder)
            .order_by(LabOrder.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(self._session.scalars(statement))
