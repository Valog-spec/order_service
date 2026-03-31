import uuid
from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException

from src.application.container import ApplicationContainer
from src.application.create_order import (
    OrderDTO,
    CreateOrderUseCase,
    InsufficientStockError,
    ItemNotFoundError,
)
from src.application.get_order import GetOrderUseCase
from src.domain.models import Order

router = APIRouter(prefix="/api")


class OrderCreateRequest(OrderDTO):
    pass


class OrderResponseModel(Order):
    pass


@router.post(
    "/orders", status_code=HTTPStatus.CREATED, response_model=OrderResponseModel
)
@inject
async def create_order(
    order: OrderCreateRequest,
    create_order_use_case: CreateOrderUseCase = Depends(
        Provide[ApplicationContainer.create_order_use_case]
    ),
):
    try:
        return await create_order_use_case(order=order)
    except InsufficientStockError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Not enough stock. Available: {e.available}, requested: {e.requested}",
        )
    except ItemNotFoundError as e:
        raise HTTPException(
            status_code=404,
            detail=f"Item not found: {e.item_id}",
        )


@router.get("/orders/{order_id}", response_model=OrderResponseModel)
@inject
async def get_order(
    order_id: uuid.UUID,
    get_order_use_case: GetOrderUseCase = Depends(
        Provide[ApplicationContainer.get_order_use_case]
    ),
):
    return await get_order_use_case(order_id=order_id)
