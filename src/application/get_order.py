import uuid
from src.domain.models import Order as DomainOrder
from src.infrastructure.unit_of_work import UnitOfWork


class GetOrderUseCase:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
    ):
        self._unit_of_work = unit_of_work

    async def __call__(self, order_id: uuid.UUID) -> DomainOrder:
        async with self._unit_of_work() as uow:
            order = await uow.orders.get_by_id(order_id=order_id)
            await uow.commit()
            return order
