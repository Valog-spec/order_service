import uuid
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import EventTypeEnum, OrderStatusEnum
from src.infrastructure.db_schema import Order, Outbox, Payment
from src.domain.models import Order as DomainOrder


class OrderRepository:
    class OrderCreateDTO(BaseModel):
        user_id: str
        quantity: int
        item_id: uuid.UUID
        idempotency_key: str

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

    async def get_by_idempotency_key(self, idempotency_key):
        result = await self._session.execute(
            select(Order).where(Order.idempotency_key == idempotency_key)
        )
        row = result.scalar_one_or_none()
        return self._construct(row)

    async def update_status(self, order_id, status):
        result = await self._session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()
        if status == "succeeded":
            status = OrderStatusEnum.PAID
        else:
            status = OrderStatusEnum.CANCELLED
        order.status = status


class PaymentRepository:
    class PaymentCreateDTO(BaseModel):
        payment_id: uuid.UUID
        order_id: uuid.UUID
        status: str
        amount: Decimal
        error_message: str | None = None

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create_from_callback(self, callback_data: PaymentCreateDTO):
        """Создает запись о платеже из callback данных"""
        payment = Payment(
            payment_id=callback_data.payment_id,
            order_id=callback_data.order_id,
            status=callback_data.status,
            amount=callback_data.amount,
            error_message=callback_data.error_message,
        )
        self._session.add(payment)

    async def get_by_payment_id(self, payment_id):
        result = await self._session.execute(
            select(Payment).where(Payment.payment_id == payment_id)
        )
        return result.scalar_one_or_none()


class OutboxRepository:
    class OrderCreateDTO(BaseModel):
        event_type: EventTypeEnum
        payload: dict

    def __init__(self, session: AsyncSession):
        self._session = session

    async def create(self, event: OrderCreateDTO):
        event = Outbox(event_type=event.event_type, payload=event.payload)

        self._session.add(event)
