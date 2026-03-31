import uuid

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import EventTypeEnum
from src.infrastructure.db_schema import Order, Outbox
from src.domain.models import Order as DomainOrder


class OrderRepository:
    class OrderCreateDTO(BaseModel):
        user_id: str
        quantity: int
        item_id: uuid.UUID
        idempotency_key: uuid.UUID

    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _construct(order_orm: Order) -> DomainOrder:
        return DomainOrder(
            id=order_orm.id,
            user_id=order_orm.user_id,
            quantity=order_orm.quantity,
            item_id=order_orm.item_id,
            status=order_orm.status,
            created_at=order_orm.created_at,
            updated_at=order_orm.updated_at,
        )

    async def create(self, order: OrderCreateDTO) -> DomainOrder:
        order = Order(
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            idempotency_key=order.idempotency_key,
        )
        self._session.add(order)
        await self._session.flush()

        return DomainOrder(
            id=order.id,
            user_id=order.user_id,
            quantity=order.quantity,
            item_id=order.item_id,
            status=order.status,
            created_at=order.created_at,
            updated_at=order.updated_at,
        )

    async def get_by_id(self, order_id: uuid.UUID) -> DomainOrder:
        result = await self._session.execute(select(Order).where(Order.id == order_id))
        row = result.scalar_one_or_none()
        return self._construct(row)


class OutboxRepository:
    class OrderCreateDTO(BaseModel):
        event_type: EventTypeEnum
        payload: dict

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: OrderCreateDTO):
        event = Outbox(event_type=event.event_type, payload=event.payload)

        self._session.add(event)
