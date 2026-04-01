import uuid
from datetime import datetime

import httpx
from pydantic import BaseModel


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
    def __init__(self, base_url: str, api_key: str, callback_url: str) -> None:
        """
        Args:
            base_url: Базовый URL провайдера (без завершающего слеша).
            api_key: Ключ аутентификации (заголовок X-Api-Key).
        """
        self._base_url = base_url
        self._api_key = api_key
        self._callback_url = callback_url

    def _headers(self) -> dict[str, str]:
        """Вернуть заголовки для аутентификации."""
        return {"X-Api-Key": self._api_key}

    async def create(self, amount, order_id, idempotency_key):
        try:
            async with httpx.AsyncClient(headers=self._headers()) as client:
                response = await client.post(
                    f"{self._base_url}/api/payments",
                    json={
                        "order_id": order_id,
                        "amount:": amount,
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

        except Exception:
            ...
