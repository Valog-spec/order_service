from sqlalchemy.orm import DeclarativeBase, relationship

import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import DateTime, String, func, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from src.domain.models import OrderStatusEnum, OutboxEventStatus, PaymentStatusEnum


class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей проекта."""


class Order(Base):
    __tablename__ = "orders"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[str] = mapped_column(nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    item_id: Mapped[uuid.UUID] = mapped_column(nullable=False)
    status: Mapped[OrderStatusEnum] = mapped_column(
        default=OrderStatusEnum.NEW, nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now()
    )
    idempotency_key: Mapped[uuid.UUID] = mapped_column(
        unique=True, nullable=False, index=True
    )

    payment: Mapped[Optional["Payment"]] = relationship(
        "Payment", back_populates="order", uselist=False, cascade="all, delete-orphan"
    )


class Outbox(Base):
    __tablename__ = "outbox"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    payload: Mapped[Dict[str, Any]] = mapped_column(JSONB, nullable=False, default={})
    status: Mapped[OutboxEventStatus] = mapped_column(
        String(20), default=OutboxEventStatus.PENDING
    )
    retry_count: Mapped[int] = mapped_column(nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )


class Payment(Base):
    __tablename__ = "payments"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    payment_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True), nullable=False, unique=True, index=True
    )
    order_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )
    status: Mapped[PaymentStatusEnum] = mapped_column(String(20), nullable=False)
    amount: Mapped[str] = mapped_column(String(20), nullable=False)

    error_message: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )

    order: Mapped["Order"] = relationship(
        "Order", back_populates="payment", uselist=False
    )
