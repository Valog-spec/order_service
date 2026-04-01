from dependency_injector import containers, providers

from src.application.callback_payment import ProcessPaymentUseCase
from src.application.create_order import CreateOrderUseCase
from src.application.get_order import GetOrderUseCase
from src.application.process_inbox_events import ProcessInboxEventsUseCase
from src.application.process_outbox_events import ProcessOutboxEventsUseCase
from src.infrastructure.container import InfrastructureContainer


class ApplicationContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    infrastructure_container = providers.Container[InfrastructureContainer](
        InfrastructureContainer,
        config=config,
    )

    create_order_use_case = providers.Singleton[CreateOrderUseCase](
        CreateOrderUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
        catalog_service=infrastructure_container.catalog_client,
        payment_service=infrastructure_container.payment_client,
    )
    get_order_use_case = providers.Singleton[GetOrderUseCase](
        GetOrderUseCase, unit_of_work=infrastructure_container.unit_of_work
    )

    process_payment_use_case = providers.Singleton[ProcessPaymentUseCase](
        ProcessPaymentUseCase, unit_of_work=infrastructure_container.unit_of_work
    )

    process_outbox_events_use_case = providers.Singleton[ProcessOutboxEventsUseCase](
        ProcessOutboxEventsUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
        kafka_producer=infrastructure_container.kafka_producer,
    )

    process_inbox_events_use_case = providers.Singleton[ProcessInboxEventsUseCase](
        ProcessInboxEventsUseCase,
        unit_of_work=infrastructure_container.unit_of_work,
        kafka_consumer=infrastructure_container.kafka_consumer,
    )
