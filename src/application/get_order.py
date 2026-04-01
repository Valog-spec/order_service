import logging
import uuid
from src.domain.models import Order as DomainOrder
from src.infrastructure.unit_of_work import UnitOfWork

logger = logging.getLogger(__name__)


class GetOrderUseCase:
    def __init__(
        self,
        unit_of_work: UnitOfWork,
    ):
        self._unit_of_work = unit_of_work

    async def __call__(self, order_id: uuid.UUID) -> DomainOrder:
        logger.info(f"Получение заказа {order_id}")
        async with self._unit_of_work() as uow:
            order = await uow.orders.get_by_id(order_id=order_id)
            if order is None:
                logger.warning(f"Заказ {order_id} не найден")
            else:
                logger.info(f"Заказ {order_id} получен")
            return order
