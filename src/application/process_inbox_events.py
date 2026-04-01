import logging
from aiokafka import AIOKafkaConsumer
from sqlalchemy.exc import IntegrityError

from src.domain.models import OrderStatusEnum
from src.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ProcessInboxEventsUseCase:
    """Обработка входящих сообщений из Kafka"""

    def __init__(
        self,
        unit_of_work: UnitOfWork,
        kafka_consumer: AIOKafkaConsumer,
    ):
        self._unit_of_work = unit_of_work
        self._consumer = kafka_consumer

    async def run(self) -> None:
        """Бесконечный цикл получения и обработки сообщений"""
        logger.info("Запуск Kafka consumer...")
        await self._consumer.start()
        async for msg in self._consumer:
            async with self._unit_of_work() as uow:
                try:
                    try:
                        await uow.inbox.add(
                            event_id=msg.key,
                            event_type=msg.value.get("event_type"),
                            payload=msg.value,
                        )
                    except IntegrityError:
                        logger.debug(f"Событие {msg.key} уже обработано")
                        await self._consumer.commit()
                        continue

                    event_type = msg.value.get("event_type")

                    if event_type == "order.shipped":
                        await self._handle_order_shipped(msg.value, uow)
                    elif event_type == "order.paid":
                        await self._handle_order_paid(msg.value, uow)
                    else:
                        logger.warning(f"Неизвестный тип события {event_type}")

                    await uow.commit()
                    await self._consumer.commit()

                    logger.info(f"Событие {msg.key} обработано")
                except Exception as e:
                    logger.error(f"Ошибка при обработке {msg.key}: {e}")
                    await uow.rollback()

    async def _handle_order_shipped(self, payload: dict, uow: UnitOfWork):
        """Обработка события order.shipped"""
        order_id = payload.get("order_id")
        logger.info(f"Статус заказа {order_id} изменен на отправлен")
        await uow.orders.update_status(
            order_id=order_id, status=OrderStatusEnum.SHIPPED
        )

    async def _handle_order_paid(self, payload: dict, uow: UnitOfWork):
        """Обработка события order.paid"""
        order_id = payload.get("order_id")
        logger.info(f"Статус заказа {order_id} изменен на оплачен")
        await uow.orders.update_status(order_id=order_id, status=OrderStatusEnum.PAID)
