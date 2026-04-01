import uuid
from http import HTTPStatus

from dependency_injector.wiring import Provide, inject
from fastapi import APIRouter, Depends, HTTPException, Response
from starlette import status

from src.application.callback_payment import PaymentDTO, ProcessPaymentUseCase
from src.application.container import ApplicationContainer
from src.application.create_order import (
    OrderDTO,
    CreateOrderUseCase,
    InsufficientStockError,
    ItemNotFoundError,
    IdempotencyConflictError,
)
from src.application.get_order import GetOrderUseCase
from src.domain.models import Order

router = APIRouter(prefix="/api")


class OrderCreateRequest(OrderDTO):
    pass


class OrderResponseModel(Order):
    pass


class PaymentCallbackRequest(PaymentDTO):
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
        return await create_order_use_case(request=order)
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
    except IdempotencyConflictError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Idempotency key '{e.key}' already used",
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


@router.post("/orders/payment-callback", status_code=HTTPStatus.OK)
@inject
async def process_payment(
    order_callback: PaymentCallbackRequest,
    callback_payment: ProcessPaymentUseCase = Depends(
        Provide[ApplicationContainer.process_payment_use_case]
    ),
):
    await callback_payment(order_callback=order_callback)
    return Response(status_code=HTTPStatus.OK)
