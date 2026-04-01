import uuid
from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel


class OrderStatusEnum(StrEnum):
    NEW = "NEW"
    PAID = "PAID"
    SHIPPED = "SHIPPED"
    CANCELLED = "CANCELLED"


class EventTypeEnum(StrEnum):
    ORDER_CREATED = "order.created"
    ORDER_PAID = "order.paid"
    ORDER_SHIPPED = "order.shipped"
    ORDER_CANCELLED = "order.cancelled"


class OutboxEventStatus(StrEnum):
    PENDING = "PENDING"
    SENT = "SENT"


class InboxEventStatus(StrEnum):
    """Статус обработки входящего события"""

    PENDING = "PENDING"
    PROCESSED = "PROCESSED"


class PaymentStatusEnum(StrEnum):
    """Статус платежа"""

    SUCCEEDED = "succeeded"
    FAILED = "failed"


class Order(BaseModel):
    id: uuid.UUID
    user_id: str
    quantity: int
    item_id: uuid.UUID
    status: OrderStatusEnum
    created_at: datetime
    updated_at: datetime


class OutboxEvent(BaseModel):
    id: str
    event_type: EventTypeEnum
    payload: dict
    status: OutboxEventStatus
    created_at: datetime
