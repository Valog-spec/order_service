import asyncio
import logging

import uvicorn
from fastapi import FastAPI

from src.application.container import ApplicationContainer
from src.config.settings import settings
from src.presentation import api
from src.presentation.api import router
from src.presentation.container import PresentationContainer
from src.presentation.outbox_worker import OutboxWorker

# from src.presentation.container import PresentationContainer
# from src.presentation.outbox_worker import OutboxWorker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)


def build_api(container: ApplicationContainer):
    logger.info("Сборка API...")
    app = FastAPI()
    app.include_router(router)
    container.wire(modules=[api])
    return app


async def main():
    logger.info("Запуск Order Service...")

    container = PresentationContainer()
    container.config.from_pydantic(settings)
    app = build_api(container.application)
    worker: OutboxWorker = container.outbox_worker()

    inbox_consumer = container.inbox_consumer()

    api_task = asyncio.create_task(
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        ).serve()
    )
    worker_task = asyncio.create_task(worker.run())
    inbox_task = asyncio.create_task(inbox_consumer.run())

    await asyncio.gather(api_task, worker_task, inbox_task)


if __name__ == "__main__":
    asyncio.run(main())
