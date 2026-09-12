from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.business_hours import (
    DEFAULT_BUSINESS_CLOSE_TIME,
    DEFAULT_BUSINESS_OPEN_TIME,
)
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
    position: Mapped[Optional[str]] = mapped_column(String(100))  # 职务（管理员注册时填写）
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
    # 经营品类，存 JSON 数组字符串（如 ["中式快餐","甜品饮品"]）
    categories: Mapped[Optional[str]] = mapped_column(Text)
    # 商家在个人中心提交、等待超管审核的资料（JSON 字符串），审核通过后覆盖正式字段
    pending_profile: Mapped[Optional[str]] = mapped_column(Text)
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
    business_open_time: Mapped[str] = mapped_column(
        String(5), default=DEFAULT_BUSINESS_OPEN_TIME,
        server_default=DEFAULT_BUSINESS_OPEN_TIME, nullable=False
    )
    business_close_time: Mapped[str] = mapped_column(
        String(5), default=DEFAULT_BUSINESS_CLOSE_TIME,
        server_default=DEFAULT_BUSINESS_CLOSE_TIME, nullable=False
    )
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
    reward_amount: Mapped[Decimal] = mapped_column(
        Numeric(10, 2), default=Decimal("0.00"), server_default="0.00", nullable=False
    )
    pickup_code: Mapped[str] = mapped_column(
        String(6), unique=True, nullable=False
    )
    status: Mapped[int] = mapped_column(default=0, nullable=False)
    picked_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    close_reason: Mapped[Optional[str]] = mapped_column(String(32))
    closed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )


class RefundApplication(Base):
    __tablename__ = "refund_applications"
    __table_args__ = (
        CheckConstraint(
            "status IN (0, 1, 2)", name="ck_refund_applications_status"
        ),
        Index("idx_refund_applications_status", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(
        ForeignKey("orders.id"), unique=True, nullable=False
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_image: Mapped[Optional[str]] = mapped_column(Text)
    status: Mapped[int] = mapped_column(default=0, nullable=False)
    admin_remark: Mapped[Optional[str]] = mapped_column(Text)
    reviewer_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)


class WalletAccount(Base):
    __tablename__ = "wallet_accounts"
    __table_args__ = (
        CheckConstraint("balance >= 0", name="ck_wallet_accounts_balance"),
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"), primary_key=True
    )
    balance: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, onupdate=now_shanghai_naive, nullable=False
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


class SubsidyGrant(Base):
    """优惠分配流水（何睿涵负责）。

    grant_type：1=发给学生（user_id 必填），2=平台注入资金（user_id 为空）。
    可分配余额 = 平台服务费累计 + 平台注入 - 已发放。
    """

    __tablename__ = "subsidy_grants"
    __table_args__ = (
        CheckConstraint("grant_type IN (1, 2)", name="ck_subsidy_grants_type"),
        Index("idx_subsidy_grants_user", "user_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    grant_type: Mapped[int] = mapped_column(nullable=False)
    user_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id")
    )
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2), default=Decimal("0.00"), nullable=False
    )
    title: Mapped[Optional[str]] = mapped_column(
        String(100), comment="学生端弹窗称号，如：本月暖心帮扶对象"
    )
    is_read: Mapped[int] = mapped_column(default=0, nullable=False)
    remark: Mapped[Optional[str]] = mapped_column(String(255))
    operator_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id")
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )


class RiskLog(Base):
    __tablename__ = "risk_logs"
    __table_args__ = (
        CheckConstraint("risk_type IN (1, 2, 3)", name="ck_risk_logs_type"),
        CheckConstraint("is_resolved IN (0, 1)", name="ck_risk_logs_resolved"),
        CheckConstraint(
            "review_status IN (0, 1, 2)", name="ck_risk_logs_review"
        ),
        Index("idx_risk_logs_product", "product_id"),
        Index("idx_risk_logs_merchant", "merchant_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        ForeignKey("products.id"), nullable=False
    )
    merchant_id: Mapped[int] = mapped_column(
        ForeignKey("merchants.id"), nullable=False
    )
    risk_type: Mapped[int] = mapped_column(nullable=False)
    risk_detail: Mapped[Optional[str]] = mapped_column(Text)
    # 风控来源：rule=本地规则引擎，ai=大模型语义审核（管理员端「AI 复核」也会刷新该字段）
    risk_source: Mapped[str] = mapped_column(
        String(16), default="rule", server_default="rule", nullable=False
    )
    is_resolved: Mapped[int] = mapped_column(default=0, nullable=False)
    # 人工复核结论：0 待人工复核 / 1 已确认拦截（同意 AI/规则判定） / 2 已误判恢复（人工放行）
    review_status: Mapped[int] = mapped_column(default=0, nullable=False)
    reviewed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    reviewer_id: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=now_shanghai_naive, nullable=False
    )
