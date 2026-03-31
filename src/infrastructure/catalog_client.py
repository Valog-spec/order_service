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

        async with httpx.AsyncClient(headers=self._headers()) as client:
            try:
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
            except Exception:
                ...
