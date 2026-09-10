from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Generic, List, Optional, TypeVar

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


class OrderOut(BaseModel):
    id: int
    product_id: int
    product_title: str
    product_image: str
    shop_name: str
    original_price: Decimal
    price: Decimal
    quantity: int
    status: int = Field(description="0 待领取，1 已领取，2 已过期")
    pickup_code: str
    expire_time: str
    location: str
    created_at: str
    picked_at: Optional[str] = None
    student_name: Optional[str] = None
    student_id: Optional[str] = None
    phone: Optional[str] = None

    @field_serializer("original_price", "price")
    def serialize_money(self, value: Decimal) -> str:
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


OrderListResponse = ApiResponse[List[OrderOut]]
