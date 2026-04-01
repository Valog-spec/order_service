from typing import Callable

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.catalog_client import HttpxCatalogClient
from src.infrastructure.kafka_consumer import KafkaConsumer
from src.infrastructure.kafka_producer import KafkaProducer
from src.infrastructure.payment_client import HttpxPaymentClient
from src.infrastructure.unit_of_work import UnitOfWork


class InfrastructureContainer(containers.DeclarativeContainer):
    config = providers.Configuration()

    async_engine = providers.Singleton[AsyncEngine](
        create_async_engine,
        config.db.DSN,
        pool_size=config.db.POOL_SIZE,
        pool_recycle=config.db.POOL_RECYCLE,
        future=True,
    )
    session_factory: Callable[..., AsyncSession] = providers.Factory(
        sessionmaker, async_engine, expire_on_commit=False, class_=AsyncSession
    )
    unit_of_work = providers.Singleton[UnitOfWork](
        UnitOfWork, session_factory=session_factory
    )
    kafka_producer = providers.Singleton[KafkaProducer](
        KafkaProducer,
        bootstrap_servers=config.kafka.KAFKA_BOOTSTRAP_SERVERS,
        topic=config.kafka.TOPIC,
    )
    kafka_consumer = providers.Singleton[KafkaConsumer](
        KafkaConsumer,
        bootstrap_servers=config.kafka.KAFKA_BOOTSTRAP_SERVERS,
        topic=config.kafka.CONSUMER_TOPIC,
        group_id=config.kafka.CONSUMER_GROUP,
    )

    catalog_client = providers.Singleton[HttpxCatalogClient](
        HttpxCatalogClient,
        base_url=config.catalog.BASE_URL,
        api_key=config.catalog.API_KEY,
    )
    payment_client = providers.Singleton[HttpxPaymentClient](
        HttpxPaymentClient,
        base_url=config.payment.BASE_URL,
        api_key=config.payment.API_KEY,
        callback_url=config.payment.CALLBACK_URL,
    )
