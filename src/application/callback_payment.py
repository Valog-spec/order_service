import logging
import uuid
from decimal import Decimal

from pydantic import BaseModel

from src.infrastructure.repositories import PaymentRepository
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
            await uow.orders.update_status(
                order_id=order_callback.order_id, status=order_callback.status
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
