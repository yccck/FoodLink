from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Generic, List, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer

T = TypeVar("T")
CENT = Decimal("0.01")


class ApiResponse(BaseModel, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class CreateOrderRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0, examples=[1], description="商品 ID")
    quantity: int = Field(
        default=1, ge=1, le=99, examples=[1], description="购买数量"
    )


class VerifyPickupCodeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    pickup_code: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        examples=["483920"],
        description="6 位数字取货码",
    )


class WalletActionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    amount: Decimal = Field(
        gt=0,
        le=Decimal("1000000.00"),
        max_digits=12,
        decimal_places=2,
        examples=["50.00"],
        description="操作金额，使用两位小数字符串传输",
    )
    payment_password: str = Field(
        min_length=6,
        max_length=6,
        pattern=r"^\d{6}$",
        examples=["123456"],
        description="比赛演示用 6 位数字支付密码",
    )


class WalletActionOut(BaseModel):
    action: Literal["recharge", "withdraw"]
    amount: Decimal
    available_balance: Decimal
    processed_at: str

    @field_serializer("amount", "available_balance")
    def serialize_money(self, value: Decimal) -> str:
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


class OrderOut(BaseModel):
    id: int
    product_id: int
    product_title: str
    product_image: str
    shop_name: str
    original_price: Decimal
    price: Decimal
    total_amount: Decimal
    quantity: int
    status: int = Field(description="0 待领取，1 已完成，2 已关闭")
    pickup_code: str
    expire_time: str
    pickup_deadline: str
    remaining_seconds: int
    location: str
    created_at: str
    picked_at: Optional[str] = None
    payment_status: str = Field(description="escrowed 托管中，settled 已结算，refunded 已退款")
    platform_fee_rate: str
    platform_fee: Decimal
    merchant_receivable: Decimal
    settled_at: Optional[str] = None
    completion_type: Optional[str] = Field(
        default=None,
        description="merchant_confirmed 商家核销，auto_timeout 6 小时超时自动完成",
    )
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    phone: Optional[str] = None

    @field_serializer(
        "original_price",
        "price",
        "total_amount",
        "platform_fee",
        "merchant_receivable",
    )
    def serialize_money(self, value: Decimal) -> str:
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


class OrderSummaryOut(BaseModel):
    role: int
    available_balance: Decimal
    escrow_amount: Decimal
    monthly_sales: Decimal
    monthly_spending: Decimal
    monthly_income: Decimal
    monthly_platform_fee: Decimal
    monthly_order_count: int
    monthly_item_count: int
    monthly_completed_count: int

    @field_serializer(
        "available_balance",
        "escrow_amount",
        "monthly_sales",
        "monthly_spending",
        "monthly_income",
        "monthly_platform_fee",
    )
    def serialize_money(self, value: Decimal) -> str:
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


OrderListResponse = ApiResponse[List[OrderOut]]
