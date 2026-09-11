from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_serializer


CENT = Decimal("0.01")


class CreateRefundApplicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reason: str = Field(
        min_length=5,
        max_length=500,
        description="食品质量问题说明，5 至 500 字",
    )
    evidence_image: Optional[str] = Field(
        default=None,
        max_length=3_000_000,
        description="可选的问题照片，演示环境支持图片 URL 或 Base64",
    )


class AuditRefundApplicationRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    audit_status: int = Field(description="1 通过并原路退款，2 驳回")
    admin_remark: str = Field(
        default="",
        max_length=500,
        description="审核说明；驳回时必填",
    )


class RefundApplicationOut(BaseModel):
    id: int
    order_id: int
    product_title: str
    product_image: str
    shop_name: str
    student_name: str
    student_id: str
    total_amount: Decimal
    reason: str
    evidence_image: str
    status: int = Field(description="0 待审核，1 已通过，2 已驳回")
    admin_remark: str
    created_at: str
    reviewed_at: Optional[str] = None

    @field_serializer("total_amount")
    def serialize_money(self, value: Decimal) -> str:
        return format(value.quantize(CENT, rounding=ROUND_HALF_UP), ".2f")
