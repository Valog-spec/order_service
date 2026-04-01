import logging
import uuid
from datetime import datetime

import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type


logger = logging.getLogger(__name__)


class RequestPayment(BaseModel):
    order_id: uuid.UUID
    amount: str
    callback_url: str
    idempotency_key: str


class ResponsePayment(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    order_id: uuid.UUID
    amount: str
    status: str
    idempotency_key: str
    created_at: datetime


class HttpxPaymentClient:
    def __init__(
        self, base_url: str, api_key: str, callback_url: str, timeout: int = 10
    ) -> None:
        """
        Args:
            base_url: Базовый URL провайдера (без завершающего слеша).
            api_key: Ключ аутентификации (заголовок X-Api-Key).
        """
        self._base_url = base_url
        self._api_key = api_key
        self._callback_url = callback_url
        self._timeout = timeout

    def _headers(self) -> dict[str, str]:
        """Вернуть заголовки для аутентификации."""
        return {"X-Api-Key": self._api_key}

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_fixed(1),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    async def create(self, amount, order_id, idempotency_key):
        try:
            async with httpx.AsyncClient(
                headers=self._headers(), timeout=self._timeout
            ) as client:
                response = await client.post(
                    f"{self._base_url}/api/payments",
                    json={
                        "order_id": str(order_id),
                        "amount": str(amount),
                        "callback_url": self._callback_url,
                        "idempotency_key": idempotency_key,
                    },
                )
                response.raise_for_status()
                data = response.json()
                return ResponsePayment(
                    id=uuid.UUID(data["id"]),
                    user_id=uuid.UUID(data["user_id"]),
                    order_id=uuid.UUID(data["order_id"]),
                    amount=data["amount"],
                    status=data["status"],
                    idempotency_key=data["idempotency_key"],
                    created_at=data["created_at"],
                )

        except httpx.TimeoutException as e:
            logger.warning(
                "Request timeout", extra={"timeout": self._timeout, "error": str(e)}
            )
            raise

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error",
                extra={
                    "status_code": e.response.status_code,
                    "response_body": e.response.text[:500],
                    "error": str(e),
                },
            )
            raise

        except Exception as e:
            logger.exception(  # Включает traceback
                "Unexpected error", extra={"error": str(e)}
            )
            raise
