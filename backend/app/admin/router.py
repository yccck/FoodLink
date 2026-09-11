"""超管后台路由（何睿涵负责）。所有接口要求 role=3。"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.admin import service
from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.errors import BusinessError
from app.schemas import (
    AdminPendingOut,
    ApiResponse,
    MerchantAuditRequest,
    MerchantPendingOut,
    MessageOut,
    RiskLogOut,
    StatisticsOut,
    UserStatusRequest,
)

router = APIRouter(tags=["超管后台"])


def require_admin(current: CurrentUser = Depends(get_current_user)) -> CurrentUser:
    if current.role != 3:
        raise BusinessError(403, "仅超管可访问", 403)
    return current


@router.get(
    "/api/admin/admins/pending",
    response_model=ApiResponse[List[AdminPendingOut]],
    summary="待审核管理员列表",
)
def pending_admins(
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[List[AdminPendingOut]]:
    return ApiResponse(data=service.list_pending_admins(db))


@router.put(
    "/api/admin/admins/{user_id}/audit",
    response_model=ApiResponse[MessageOut],
    summary="审核管理员（通过/驳回）",
)
def audit_admin(
    user_id: int,
    request: MerchantAuditRequest,
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[MessageOut]:
    service.audit_admin_user(db, user_id, request.audit_status)
    msg = "审核通过，该管理员可登录" if request.audit_status == 1 else "已驳回并删除该申请"
    return ApiResponse(data=MessageOut(message=msg))


@router.get(
    "/api/admin/merchants/pending",
    response_model=ApiResponse[List[MerchantPendingOut]],
    summary="待审核商家列表",
)
def pending_merchants(
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[List[MerchantPendingOut]]:
    return ApiResponse(data=service.list_pending_merchants(db))


@router.put(
    "/api/admin/merchants/{merchant_id}/audit",
    response_model=ApiResponse[MessageOut],
    summary="审核商家（通过/驳回）",
)
def audit_merchant(
    merchant_id: int,
    request: MerchantAuditRequest,
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[MessageOut]:
    service.audit_merchant(db, merchant_id, request.audit_status)
    msg = "审核通过" if request.audit_status == 1 else "已驳回"
    return ApiResponse(data=MessageOut(message=msg))


@router.get(
    "/api/admin/risk-logs",
    response_model=ApiResponse[List[RiskLogOut]],
    summary="风控日志列表",
)
def risk_logs(
    is_resolved: Optional[int] = Query(None, description="0 未处理，1 已处理，不传查全部"),
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[List[RiskLogOut]]:
    return ApiResponse(data=service.list_risk_logs(db, is_resolved))


@router.put(
    "/api/admin/risk-logs/{log_id}/resolve",
    response_model=ApiResponse[MessageOut],
    summary="标记风控日志已处理",
)
def resolve_risk_log(
    log_id: int,
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[MessageOut]:
    service.resolve_risk_log(db, log_id)
    return ApiResponse(data=MessageOut(message="已处理"))


@router.put(
    "/api/admin/users/{user_id}/status",
    response_model=ApiResponse[MessageOut],
    summary="禁用 / 启用用户",
)
def set_user_status(
    user_id: int,
    request: UserStatusRequest,
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[MessageOut]:
    service.set_user_status(db, user_id, request.status)
    msg = "已禁用" if request.status == 0 else "已启用"
    return ApiResponse(data=MessageOut(message=msg))


@router.get(
    "/api/admin/statistics",
    response_model=ApiResponse[StatisticsOut],
    summary="平台数据看板",
)
def statistics(
    _: CurrentUser = Depends(require_admin),
    db: Session = Depends(get_db),
) -> ApiResponse[StatisticsOut]:
    return ApiResponse(data=service.get_statistics(db))
