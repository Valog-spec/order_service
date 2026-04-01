import logging

from src.infrastructure.kafka_producer import KafkaProducer
from src.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class ProcessOutboxEventsUseCase:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        kafka_producer: KafkaProducer,
        batch_size: int = 100,
    ):
        self._unit_of_work = unit_of_work
        self._kafka_producer = kafka_producer
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
                        await kp.send_message(
                            message={
                                "payload": event.payload,
                            },
                            key=event.id,
                        )
                    except Exception as e:
                        logger.warning(f"Failed to send event {event.id}: {e}")
                        continue

                    await uow.outbox.mark_as_sent(event.id)

                    await uow.commit()
