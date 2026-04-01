import asyncio
import logging

import uvicorn
from fastapi import FastAPI

from src.application.container import ApplicationContainer
from src.config.settings import settings
from src.presentation import api
from src.presentation.api import router
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
    # presentation_container = PresentationContainer()
    # presentation_container.config.from_yaml("app/config.yaml", required=True)
    #
    # app = build_api(presentation_container.application)
    # # worker: OutboxWorker = presentation_container.outbox_worker()
    #
    # api_task = asyncio.create_task(
    #     uvicorn.Server(
    #         uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
    #     ).serve()
    # )
    #
    # # worker_task = asyncio.create_task(worker.run())
    #
    # await asyncio.gather(api_task, worker_task)
    container = ApplicationContainer()
    container.config.from_pydantic(settings)
    # 2. Собираем API
    app = build_api(container)

    api_task = asyncio.create_task(
        uvicorn.Server(
            uvicorn.Config(app, host="0.0.0.0", port=8000, log_level="info")
        ).serve()
    )

    await asyncio.gather(api_task)


if __name__ == "__main__":
    asyncio.run(main())
