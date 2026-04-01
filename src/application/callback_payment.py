import logging
import uuid
from decimal import Decimal

from pydantic import BaseModel

from src.domain.models import EventTypeEnum
from src.infrastructure.repositories import PaymentRepository, OutboxRepository
from src.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class PaymentDTO(BaseModel):
    payment_id: uuid.UUID
    order_id: uuid.UUID
    status: str
    amount: Decimal
    error_message: str | None = None


class ProcessPaymentUseCase:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
    ):
        self._unit_of_work = unit_of_work

    async def __call__(self, order_callback: PaymentDTO):
        logger.info(
            f"Обработка callback платежа {order_callback.payment_id} для заказа {order_callback.order_id}"
        )
        async with self._unit_of_work() as uow:
            existing_payment = await uow.payments.get_by_payment_id(
                order_callback.payment_id
            )
            if existing_payment:
                logger.info(f"Платеж {order_callback.payment_id} уже обработан")
                return
            logger.info(
                f"Обновление статуса заказа {order_callback.order_id} на {order_callback.status}"
            )
            order = await uow.orders.get_by_id(order_id=order_callback.order_id)
            if not order:
                logger.error(f"Заказ {order_callback.order_id} не найден")
                raise

            await uow.orders.update_status(
                order_id=order_callback.order_id, status=order_callback.status
            )
            if order_callback.status == "succeeded":
                event_type = EventTypeEnum.ORDER_PAID
                event_name = "order.paid"
            else:
                event_type = EventTypeEnum.ORDER_CANCELLED
                event_name = "order.cancelled"

            await uow.outbox.create(
                event=OutboxRepository.OrderCreateDTO(
                    event_type=event_type,
                    payload={
                        "event_type": event_name,
                        "order_id": str(order_callback.order_id),
                        "item_id": str(order.item_id),
                        "quantity": order.quantity,
                        "idempotency_key": order.idempotency_key,
                    },
                )
            )
            logger.info(f"Сохранение платежа {order_callback.payment_id}")
            await uow.payments.create_from_callback(
                callback_data=PaymentRepository.PaymentCreateDTO(
                    payment_id=order_callback.payment_id,
                    order_id=order_callback.order_id,
                    status=order_callback.status,
                    amount=order_callback.amount,
                    error_message=order_callback.error_message,
                )
            )
            await uow.commit()
