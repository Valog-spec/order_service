import logging

from src.infrastructure.kafka_producer import KafkaProducer
from src.infrastructure.notification_client import HttpxNotificationClient
from src.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ProcessOutboxEventsUseCase:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        kafka_producer: KafkaProducer,
        notification_client: HttpxNotificationClient,
        batch_size: int = 100,
    ):
        self._unit_of_work = unit_of_work
        self._kafka_producer = kafka_producer
        self._notification_client = notification_client
        self._batch_size = batch_size

    async def __call__(self) -> None:

        async with self._unit_of_work() as uow:
            events = await uow.outbox.get_pending_events(limit=self._batch_size)

            if not events:
                logger.debug("Нет событий для отправки")
                return

        async with self._kafka_producer as kp:
            for event in events:
                async with self._unit_of_work() as uow:
                    try:
                        logger.debug(
                            f"Отправка события {event.id} типа {event.event_type}"
                        )
                        await kp.send_message(
                            message=event.payload,
                            key=event.id,
                        )
                        logger.debug(f"Событие {event.id} отправлено")
                    except Exception as e:
                        logger.warning(f"Failed to send event {event.id}: {e}")
                        continue
                    await self._send_notification(event)

                    await uow.outbox.mark_as_sent(event.id)

                    await uow.commit()

    async def _send_notification(self, event):
        """Отправляет уведомление для событий заказа"""
        payload = event.payload
        event_type = payload.get("event_type")
        logger.info(f"Обработка уведомления для события: {event_type}")
        messages = {
            "order.created": "Your order has been created",
            "order.paid": "Your order has been paid",
            "order.shipped": "Your order has been shipped!",
            "order.cancelled": "Your order has been cancelled",
        }

        message = messages.get(event_type)
        if not message:
            logger.debug(f"Нет уведомления для {event_type}")
            return

        reference_id = payload.get("order_id")
        idempotency_key = payload.get("idempotency_key")
        logger.info(
            f"Отправка в сервис уведомлений: сообщение='{message}', заказ={reference_id}, ключ идемпотентности={idempotency_key}"
        )
        try:
            await self._notification_client.send(
                message=message,
                reference_id=reference_id,
                idempotency_key=idempotency_key,
            )
            logger.info(f"Уведомление для заказа {reference_id} успешно отправлено")
        except Exception as e:
            logger.error(
                f"Не удалось отправить уведомление для заказа {reference_id}: {e}"
            )
