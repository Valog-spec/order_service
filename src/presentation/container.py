from dependency_injector import containers, providers

from src.application.container import ApplicationContainer
from src.presentation.kafka_consumer_worker import InboxConsumer
from src.presentation.outbox_worker import OutboxWorker


class PresentationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    application = providers.Container[ApplicationContainer](
        ApplicationContainer, config=config
    )

    outbox_worker = providers.Singleton[OutboxWorker](
        OutboxWorker, use_case=application.process_outbox_events_use_case
    )

    inbox_consumer = providers.Singleton[InboxConsumer](
        InboxConsumer,
        use_case=application.process_inbox_events_use_case,
    )
