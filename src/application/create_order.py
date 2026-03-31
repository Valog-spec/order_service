from pydantic import BaseModel
import uuid

from src.domain.models import Order as DomainOrder, EventTypeEnum
from src.infrastructure.catalog_client import HttpxCatalogClient
from src.infrastructure.repositories import OrderRepository, OutboxRepository
from src.infrastructure.unit_of_work import UnitOfWork


class OrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: uuid.UUID
    idempotency_key: uuid.UUID


class InsufficientStockError(Exception):
    """Исключение: недостаточно товара на складе"""

    def __init__(self, available: int, requested: int, item_id: str):
        self.available = available
        self.requested = requested
        self.item_id = item_id
        super().__init__(
            f"Item {item_id}: available {available}, requested {requested}"
        )


class ItemNotFoundError(Exception):
    """Исключение: товар не найден в каталоге"""

    def __init__(self, item_id: str):
        self.item_id = item_id
        super().__init__(f"Item {item_id} not found in catalog")


class CreateOrderUseCase:
    def __init__(self, unit_of_work: UnitOfWork, catalog_service: HttpxCatalogClient):
        self._unit_of_work = unit_of_work
        self._catalog_service = catalog_service

    async def __call__(self, order: OrderDTO) -> DomainOrder:
        catalog_item = await self._catalog_service.get_by_id(order.item_id)

        if catalog_item is None:
            raise ItemNotFoundError(item_id=str(order.item_id))

        if catalog_item.available_qty < order.quantity:
            raise InsufficientStockError(
                available=catalog_item.available_qty,
                requested=order.quantity,
                item_id=str(order.item_id),
            )

        async with self._unit_of_work() as uow:
            order = await uow.orders.create(
                order=OrderRepository.OrderCreateDTO(
                    user_id=order.user_id,
                    quantity=order.quantity,
                    item_id=order.item_id,
                    idempotency_key=order.idempotency_key,
                )
            )
            await uow.outbox.create(
                event=OutboxRepository.OrderCreateDTO(
                    event_type=EventTypeEnum.ORDER_CREATED,
                    payload=order.model_dump(mode="json"),
                )
            )
            await uow.commit()
            return order
