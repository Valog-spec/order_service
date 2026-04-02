import logging

import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    retry_if_exception_type,
    wait_exponential,
)

logger = logging.getLogger(__name__)


class HttpxNotificationClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 30):
        self._base_url = base_url
        self._api_key = api_key
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        return {"X-API-Key": self._api_key}

    @retry(
        stop=stop_after_attempt(7),
        wait=wait_exponential(multiplier=1, min=1, max=8),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def send(self, message: str, reference_id: str, idempotency_key: str):
        """Отправляет уведомление"""
        logger.info(f"Отправка уведомления для заказа {reference_id}")
        async with httpx.AsyncClient(
            headers=self._headers(), timeout=self._timeout
        ) as client:
            response = await client.post(
                f"{self._base_url}/api/notifications",
                json={
                    "message": message,
                    "reference_id": reference_id,
                    "idempotency_key": idempotency_key,
                },
            )
            logger.info(f"Статус ответа от сервиса уведомлений: {response.status_code}")
            try:
                response.raise_for_status()
            except httpx.HTTPStatusError as e:
                logger.error(
                    f"Ошибка при отправке уведомления: {e.response.status_code} - {e.response.text}"
                )
                raise
            except Exception as e:
                logger.error(f"Неизвестная ошибка при отправке уведомления: {e}")
                raise

            logger.info(f"Уведомление для заказа {reference_id} успешно отправлено")
