import logging
from src.application.process_inbox_events import ProcessInboxEventsUseCase

logger = logging.getLogger(__name__)


class InboxConsumer:
    def __init__(self, use_case: ProcessInboxEventsUseCase):
        self._use_case = use_case

    async def run(self):
        logger.info("Запуск Inbox consumer...")
        await self._use_case.run()
