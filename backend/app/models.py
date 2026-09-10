from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.timeutils import now_shanghai_naive


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint("role IN (1, 2, 3)", name="ck_users_role"),
        CheckConstraint("status IN (0, 1)", name="ck_users_status"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    role: Mapped[int] = mapped_column(nullable=False)
    login_name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    school: Mapped[Optional[str]] = mapped_column(String(200))
    student_id: Mapped[Optional[str]] = mapped_column(String(100), unique=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    phone: Mapped[str] = mapped_column(String(30), nullable=False)
    avatar: Mapped[Optional[str]] = mapped_column(Text)
    preferences: Mapped[Optional[str]] = mapped_column(Text)
    taboo: Mapped[Optional[str]] = mapped_column(Text)
    monthly_budget: Mapped[Optional[Decimal]] = mapped_column(Numeric(10, 2))
    status: Mapped[int] = mapped_column(default=1, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )


class Merchant(Base):
    __tablename__ = "merchants"
    __table_args__ = (
        CheckConstraint(
            "audit_status IN (0, 1, 2)", name="ck_merchants_audit_status"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), unique=True, nullable=False
    )
    shop_name: Mapped[str] = mapped_column(String(200), nullable=False)
    license_img: Mapped[Optional[str]] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    lng: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    audit_status: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("quantity >= 0", name="ck_products_quantity"),
        CheckConstraint("status IN (0, 1, 2, 3)", name="ck_products_status"),
        Index("idx_products_merchant", "merchant_id"),
        Index("idx_products_status_expire", "status", "expire_time"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.id"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    category: Mapped[Optional[str]] = mapped_column(String(100))
    image: Mapped[Optional[str]] = mapped_column(Text)
    original_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    discount_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    expire_time: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=False)
    lat: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    lng: Mapped[Decimal] = mapped_column(Numeric(10, 6), nullable=False)
    status: Mapped[int] = mapped_column(default=1, nullable=False)
    view_count: Mapped[int] = mapped_column(default=0, nullable=False)
    fav_count: Mapped[int] = mapped_column(default=0, nullable=False)
    order_count: Mapped[int] = mapped_column(default=0, nullable=False)
    risk_flag: Mapped[int] = mapped_column(default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_orders_quantity"),
        CheckConstraint("status IN (0, 1, 2)", name="ck_orders_status"),
        CheckConstraint("length(pickup_code) = 6", name="ck_orders_pickup_code"),
        Index("idx_orders_user_status", "user_id", "status"),
        Index("idx_orders_product", "product_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )
    quantity: Mapped[int] = mapped_column(default=1, nullable=False)
    original_price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2), nullable=False)
    pickup_code: Mapped[str] = mapped_column(
        String(6), unique=True, nullable=False
    )
    status: Mapped[int] = mapped_column(default=0, nullable=False)
    picked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )


class Behavior(Base):
    __tablename__ = "behaviors"
    __table_args__ = (
        CheckConstraint(
            "behavior_type IN (1, 2, 3, 4)", name="ck_behaviors_type"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )
    behavior_type: Mapped[int] = mapped_column(nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )
