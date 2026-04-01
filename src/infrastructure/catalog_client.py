import logging
import uuid
from datetime import datetime
from decimal import Decimal

import httpx
from pydantic import BaseModel
from tenacity import retry, stop_after_attempt, wait_fixed, retry_if_exception_type


class CatalogResponse(BaseModel):
    id: uuid.UUID
    name: str
    price: Decimal
    available_qty: int
    created_at: datetime


logger = logging.getLogger(__name__)


class HttpxCatalogClient:
    def __init__(self, base_url: str, api_key: str, timeout: int = 10) -> None:
        """
        Args:
            base_url: Базовый URL провайдера (без завершающего слеша).
            api_key: Ключ аутентификации (заголовок X-Api-Key).
        """
        self._base_url = base_url
        self._api_key = api_key
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
    async def get_by_id(self, item_id: uuid.UUID) -> CatalogResponse:
        try:
            async with httpx.AsyncClient(
                headers=self._headers(), timeout=self._timeout
            ) as client:
                response = await client.get(
                    f"{self._base_url}/api/catalog/items/{item_id}"
                )
                response.raise_for_status()
                data = response.json()
                return CatalogResponse(
                    id=uuid.UUID(data["id"]),
                    name=data["name"],
                    price=Decimal(data["price"]),
                    available_qty=data["available_qty"],
                    created_at=datetime.fromisoformat(
                        data["created_at"].replace("Z", "+00:00")
                    ),
                )
        except httpx.TimeoutException as e:
            logger.warning(
                "Request timeout",
                extra={
                    "item_id": str(item_id),
                    "timeout": self._timeout,
                    "error": str(e),
                },
            )
            raise

        except httpx.HTTPStatusError as e:
            logger.error(
                "HTTP error",
                extra={
                    "item_id": str(item_id),
                    "status_code": e.response.status_code,
                    "response_body": e.response.text[:500],
                    "error": str(e),
                },
            )
            raise

        except Exception as e:
            logger.exception(  # Включает traceback
                "Unexpected error", extra={"item_id": str(item_id), "error": str(e)}
            )
            raise
