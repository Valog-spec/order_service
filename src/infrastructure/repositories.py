import logging
import uuid
from decimal import Decimal

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.models import (
    EventTypeEnum,
    OrderStatusEnum,
    OutboxEventStatus,
    OutboxEvent,
)
from src.infrastructure.db_schema import Order, Outbox, Payment, Inbox
from src.domain.models import Order as DomainOrder

logger = logging.getLogger(__name__)


class OrderRepository:
    class OrderCreateDTO(BaseModel):
        user_id: str
        quantity: int
        item_id: uuid.UUID
        idempotency_key: str

    def __init__(self, session: AsyncSession):
        self._session = session

    @staticmethod
    def _construct(order_orm: Order | None) -> DomainOrder | None:
        if not order_orm:
            return None
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

    async def update_status(self, order_id, status: OrderStatusEnum):
        logger.info(f"Обновление статуса заказа {order_id} на {status}")

        result = await self._session.execute(select(Order).where(Order.id == order_id))
        order = result.scalar_one_or_none()

        if not order:
            logger.error(f"Заказ {order_id} не найден при обновлении статуса")
            return

        old_status = order.status
        order.status = status

        logger.info(f"Статус заказа {order_id} изменен: {old_status} → {order.status}")


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

    @staticmethod
    def _construct(outbox: Outbox | None) -> OutboxEvent | None:
        if not outbox:
            return None

        return OutboxEvent(
            id=str(outbox.id),
            event_type=outbox.event_type,
            payload=outbox.payload,
            status=outbox.status,
            created_at=outbox.created_at,
        )

    async def create(self, event: OrderCreateDTO):
        event = Outbox(event_type=event.event_type, payload=event.payload)
        self._session.add(event)

    async def get_pending_events(self, limit: int = 100) -> list[OutboxEvent]:
        stmt = (
            select(Outbox)
            .where(Outbox.status == OutboxEventStatus.PENDING)
            .order_by(Outbox.created_at)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        rows = result.scalars().all()

        return [self._construct(row) for row in rows]

    async def mark_as_sent(self, event_id):
        result = await self._session.execute(
            select(Outbox).where(Outbox.id == event_id)
        )
        order = result.scalar_one_or_none()
        order.status = OutboxEventStatus.SENT


class InboxRepository:
    class OrderCreateDTO(BaseModel):
        event_type: EventTypeEnum
        payload: dict

    def __init__(self, session: AsyncSession):
        self._session = session

    async def add(self, event_id, event_type, payload):
        inbox_entry = Inbox(
            event_id=event_id,
            event_type=event_type,
            payload=payload,
        )
        self._session.add(inbox_entry)
        try:
            await self._session.flush()
        except IntegrityError:
            raise
