from typing import Callable

from dependency_injector import containers, providers
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from src.infrastructure.catalog_client import HttpxCatalogClient
from src.infrastructure.unit_of_work import UnitOfWork


class InfrastructureContainer(containers.DeclarativeContainer):
    config = providers.Configuration()
    # async_engine = providers.Singleton[AsyncEngine](
    #     create_async_engine,
    #     providers.Callable(
    #         lambda db: f"postgresql+asyncpg://{db['USER']}:{db['PASSWORD']}@{db['HOST']}:{db['PORT']}/{db['NAME']}",
    #         config.db,
    #     ),
    #     pool_size=config.db.POOL_SIZE,
    #     pool_recycle=config.db.POOL_RECYCLE,
    #     future=True,
    # )
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
    # kafka_producer = providers.Singleton[KafkaProducer](
    #     KafkaProducer,
    #     bootstrap_servers=config.kafka.bootstrap_servers,
    #     topic=config.kafka.topic,
    # )

    catalog_client = providers.Singleton[HttpxCatalogClient](
        HttpxCatalogClient,
        base_url=config.catalog.BASE_URL,
        api_key=config.catalog.API_KEY,
    )
