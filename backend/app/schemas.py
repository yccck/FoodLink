from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, field_serializer

from app.business_hours import (
    DEFAULT_BUSINESS_CLOSE_TIME,
    DEFAULT_BUSINESS_OPEN_TIME,
)

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
    total_amount: Decimal
    quantity: int
    status: int = Field(description="0 待领取，1 已完成，2 已关闭")
    pickup_code: str
    expire_time: str
    business_open_time: str
    business_close_time: str
    pickup_deadline: str
    remaining_seconds: int
    refund_deadline: str
    refundable: bool
    location: str
    created_at: str
    picked_at: Optional[str] = None
    payment_status: str = Field(description="paid 已支付，settled 已结算，refunded 已退款")
    platform_fee_rate: str
    platform_fee: Decimal
    merchant_receivable: Decimal
    settled_at: Optional[str] = None
    completion_type: Optional[str] = Field(
        default=None,
        description="merchant_confirmed 商家核销，auto_timeout 到关门时间自动完成",
    )
    close_reason: Optional[str] = Field(
        default=None,
        description="product_expired 食品领取期限已过，student_refund 学生限时取消，admin_refund 管理员审核退款",
    )
    closed_at: Optional[str] = None
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
    monthly_sales: Decimal
    monthly_spending: Decimal
    monthly_income: Decimal
    monthly_platform_fee: Decimal
    monthly_order_count: int
    monthly_item_count: int
    monthly_completed_count: int

    @field_serializer(
        "monthly_sales",
        "monthly_spending",
        "monthly_income",
        "monthly_platform_fee",
    )
    def serialize_money(self, value: Decimal) -> str:
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


OrderListResponse = ApiResponse[List[OrderOut]]


# ======================================================================
# 认证模块 DTO（何睿涵）
# ======================================================================


class LoginRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    login_name: str = Field(min_length=1, examples=["2021001"], description="登录账号（学生=学号，商家=自定义账号，超管=admin）")
    password: str = Field(min_length=1, examples=["123456"], description="密码")
    role: int = Field(examples=[1], description="角色：1 学生，2 商家，3 超管")


class RegisterRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: int = Field(examples=[1], description="角色：1 学生，2 商家，3 管理员")
    # 学生字段
    school: Optional[str] = None
    student_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    # 管理员字段
    position: Optional[str] = None
    # 商家字段
    shop_name: Optional[str] = None
    license_img: Optional[str] = None
    location: Optional[str] = None
    lat: Optional[Decimal] = None
    lng: Optional[Decimal] = None
    login_name: Optional[str] = None


class ResetPasswordRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    role: int = Field(examples=[1], description="角色：1 学生，2 商家，3 管理员")
    # 学生验证：学号 + 姓名 + 手机号
    student_id: Optional[str] = None
    name: Optional[str] = None
    phone: Optional[str] = None
    # 商家验证：账号 + 店名 + 手机号；管理员验证：账号 + 姓名 + 手机号
    login_name: Optional[str] = None
    shop_name: Optional[str] = None


class UserOut(BaseModel):
    id: int
    role: int
    login_name: str
    name: str
    avatar: str = ""
    school: str = ""
    student_id: str = ""
    position: str = ""
    phone: str
    preferences: dict = Field(default_factory=dict)
    taboo: dict = Field(default_factory=dict)
    monthly_budget: Optional[Decimal] = None
    status: int
    shop_name: str = ""
    license_img: str = ""
    audit_status: int = Field(default=-1, description="非商家为 -1；商家 0待审核 1通过 2驳回")

    @field_serializer("monthly_budget")
    def serialize_budget(self, value: Optional[Decimal]) -> Optional[str]:
        if value is None:
            return None
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


class LoginOut(BaseModel):
    token: str
    user: UserOut


class RegisterOut(BaseModel):
    id: int
    audit_status: Optional[int] = None


class MessageOut(BaseModel):
    message: str


class ProfileUpdateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = None
    phone: Optional[str] = None
    avatar: Optional[str] = None
    preferences: Optional[dict] = None
    taboo: Optional[dict] = None
    monthly_budget: Optional[Decimal] = None


# ======================================================================
# 商品模块 DTO（何睿涵）
# ======================================================================


class ProductCreateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = None
    image: Optional[str] = ""
    original_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    discount_price: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    quantity: int = Field(default=1, ge=0)
    expire_time: str = Field(examples=["2026-09-11 18:00:00"], description="截止有效期 yyyy-MM-dd HH:mm:ss")
    business_open_time: str = Field(
        default=DEFAULT_BUSINESS_OPEN_TIME,
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
        description="每日开门时间 HH:mm",
    )
    business_close_time: str = Field(
        default=DEFAULT_BUSINESS_CLOSE_TIME,
        pattern=r"^(?:[01]\d|2[0-3]):[0-5]\d$",
        description="每日关门时间 HH:mm，也是订单领取截止时间",
    )
    location: str
    lat: Decimal
    lng: Decimal


class MerchantBriefOut(BaseModel):
    id: int
    shop_name: str
    location: str = ""


class ProductOut(BaseModel):
    id: int
    merchant_id: int
    title: str
    description: Optional[str] = None
    category: Optional[str] = None
    image: str = ""
    original_price: Decimal
    discount_price: Decimal
    quantity: int
    expire_time: str
    business_open_time: str
    business_close_time: str
    location: str
    lat: Decimal
    lng: Decimal
    status: int
    view_count: int
    fav_count: int
    order_count: int
    created_at: str
    distance: Optional[float] = None
    is_favorite: Optional[bool] = None
    match_tags: Optional[List[str]] = None
    merchant: Optional[MerchantBriefOut] = None

    @field_serializer("original_price", "discount_price")
    def serialize_money(self, value: Decimal) -> str:
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")


class ProductPageOut(BaseModel):
    total: int
    page: int
    size: int
    items: List[ProductOut]


class FavoriteRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    favorite: bool = Field(description="true 收藏，false 取消收藏")


class FavoriteOut(BaseModel):
    favorite: bool
    fav_count: int


class BehaviorRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    product_id: int = Field(gt=0)
    behavior_type: int = Field(description="1浏览 2收藏 3下单 4分享")


# ======================================================================
# 超管后台 DTO（何睿涵）
# ======================================================================


class MerchantAuditRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_status: int = Field(description="1 通过，2 驳回")


class UserStatusRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    status: int = Field(description="1 正常，0 禁用")


class MerchantPendingOut(BaseModel):
    id: int
    user_id: int
    shop_name: str
    license_img: str = ""
    location: str
    login_name: str
    phone: str
    created_at: str


class AdminPendingOut(BaseModel):
    id: int
    school: str = ""
    name: str = ""
    position: str = ""
    login_name: str
    phone: str
    created_at: str


class RiskLogOut(BaseModel):
    id: int
    product_id: int
    product_title: str
    merchant_id: int
    shop_name: str
    risk_type: int = Field(description="1价格 2敏感词 3有效期")
    risk_detail: str
    is_resolved: int
    created_at: str


class StatisticsOut(BaseModel):
    total_users: int
    total_students: int
    total_merchants: int
    pending_merchants: int
    total_products: int
    on_sale_products: int
    total_orders: int
    risk_blocked_products: int
    unresolved_risk_logs: int
