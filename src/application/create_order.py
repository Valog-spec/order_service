from pydantic import BaseModel
import uuid

from src.domain.models import Order as DomainOrder, EventTypeEnum
from src.infrastructure.catalog_client import HttpxCatalogClient
from src.infrastructure.payment_client import HttpxPaymentClient
from src.infrastructure.repositories import OrderRepository, OutboxRepository
from src.infrastructure.unit_of_work import UnitOfWork


class OrderDTO(BaseModel):
    user_id: str
    quantity: int
    item_id: uuid.UUID
    idempotency_key: str


class IdempotencyConflictError(Exception):
    """Ошибка: ключ идемпотентности уже используется с другими данными"""

    def __init__(self, key: str):
        self.key = key
        super().__init__(f"Idempotency key '{key}' already used")


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
    def __init__(
        self,
        unit_of_work: UnitOfWork,
        catalog_service: HttpxCatalogClient,
        payment_service: HttpxPaymentClient,
    ):
        self._unit_of_work = unit_of_work
        self._catalog_service = catalog_service
        self._payment_service = payment_service

    async def __call__(self, request: OrderDTO) -> DomainOrder:
        catalog_item = await self._catalog_service.get_by_id(request.item_id)

        if catalog_item is None:
            raise ItemNotFoundError(item_id=str(request.item_id))

        if catalog_item.available_qty < request.quantity:
            raise InsufficientStockError(
                available=catalog_item.available_qty,
                requested=request.quantity,
                item_id=str(request.item_id),
            )

        async with self._unit_of_work() as uow:
            existing_order = await uow.orders.get_by_idempotency_key(
                request.idempotency_key
            )
            if existing_order:
                if (
                    existing_order.user_id == request.user_id
                    and existing_order.quantity == request.quantity
                    and existing_order.item_id == request.item_id
                ):
                    return existing_order
                else:
                    raise IdempotencyConflictError(key=request.idempotency_key)

            order = await uow.orders.create(
                order=OrderRepository.OrderCreateDTO(
                    user_id=request.user_id,
                    quantity=request.quantity,
                    item_id=request.item_id,
                    idempotency_key=request.idempotency_key,
                )
            )
            await self._payment_service.create(
                catalog_item.price, order.id, request.idempotency_key
            )

            await uow.outbox.create(
                event=OutboxRepository.OrderCreateDTO(
                    event_type=EventTypeEnum.ORDER_CREATED,
                    payload=order.model_dump(mode="json"),
                )
            )
            await uow.commit()
            return order
