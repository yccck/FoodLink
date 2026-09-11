from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.refunds import service
from app.refunds.schemas import (
    AuditRefundApplicationRequest,
    CreateRefundApplicationRequest,
    RefundApplicationOut,
)
from app.schemas import ApiResponse


student_router = APIRouter(prefix="/api/orders", tags=["订单售后"])
admin_router = APIRouter(prefix="/api/admin/refund-requests", tags=["退款审核"])


@student_router.get(
    "/refund-requests",
    response_model=ApiResponse[List[RefundApplicationOut]],
    response_model_exclude_none=True,
    summary="查看我的食品问题售后申请",
)
def list_my_refund_applications(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[RefundApplicationOut]]:
    return ApiResponse(
        data=service.list_student_refund_applications(db, current_user)
    )


@student_router.post(
    "/{order_id}/refund-request",
    response_model=ApiResponse[RefundApplicationOut],
    response_model_exclude_none=True,
    summary="提交食品问题退款申请",
    description="仅限商家实际核销后的食品质量问题；提交后由管理员审核。",
)
def create_refund_application(
    request: CreateRefundApplicationRequest,
    order_id: int = Path(gt=0, description="订单 ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[RefundApplicationOut]:
    return ApiResponse(
        data=service.create_refund_application(
            db, current_user, order_id, request
        )
    )


@admin_router.get(
    "",
    response_model=ApiResponse[List[RefundApplicationOut]],
    response_model_exclude_none=True,
    summary="查询食品问题退款申请",
)
def list_refund_applications(
    status: Optional[int] = Query(
        default=None, description="0 待审核，1 已通过，2 已驳回；不传查全部"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[RefundApplicationOut]]:
    return ApiResponse(
        data=service.list_admin_refund_applications(db, current_user, status)
    )


@admin_router.put(
    "/{application_id}/audit",
    response_model=ApiResponse[RefundApplicationOut],
    response_model_exclude_none=True,
    summary="审核食品问题退款申请",
)
def audit_refund_application(
    request: AuditRefundApplicationRequest,
    application_id: int = Path(gt=0, description="退款申请 ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[RefundApplicationOut]:
    return ApiResponse(
        data=service.audit_refund_application(
            db,
            current_user,
            application_id,
            request.audit_status,
            request.admin_remark,
        )
    )
