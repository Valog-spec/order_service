import asyncio
import logging
import uuid
from datetime import datetime

import httpx
from pydantic import BaseModel


class CatalogResponse(BaseModel):
    id: uuid.UUID
    name: str
    price: int
    available_qty: int
    created_at: datetime


logger = logging.getLogger(__name__)


class HttpxCatalogClient:
    def __init__(self, base_url: str, api_key: str) -> None:
        """
        Args:
            base_url: Базовый URL провайдера (без завершающего слеша).
            api_key: Ключ аутентификации (заголовок X-Api-Key).
        """
        self._base_url = base_url
        self._api_key = api_key

    def _headers(self) -> dict[str, str]:
        """Вернуть заголовки для аутентификации."""
        return {"X-Api-Key": self._api_key}

    async def get_by_id(self, item_id: uuid.UUID):
        for attempt in range(1, 4):
            try:
                async with httpx.AsyncClient(headers=self._headers()) as client:
                    response = await client.get(
                        f"{self._base_url}/api/catalog/items/{item_id}"
                    )
                    response.raise_for_status()
                    data = response.json()
                    return CatalogResponse(
                        id=uuid.UUID(data["id"]),
                        name=data["name"],
                        price=int(data["price"]),
                        available_qty=data["available_qty"],
                        created_at=datetime.fromisoformat(
                            data["created_at"].replace("Z", "+00:00")
                        ),
                    )
            except Exception as e:
                logger.warning(f"Attempt {attempt} failed for item {item_id}: {e}")
                if attempt == 3:
                    logger.error(f"All 3 attempts failed for item {item_id}")
                    return None
                await asyncio.sleep(1)
