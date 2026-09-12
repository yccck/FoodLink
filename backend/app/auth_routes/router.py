"""认证模块路由：登录 / 注册 / 重置密码 / 个人资料 / 行为记录。

登录、注册、重置密码为公开接口；个人资料与行为记录需携带 Token。
"""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.auth_routes import service
from app.database import get_db
from app.schemas import (
    ApiResponse,
    BehaviorRequest,
    LoginOut,
    LoginRequest,
    MessageOut,
    ProfileUpdateRequest,
    RegisterOut,
    RegisterRequest,
    ResetPasswordRequest,
    SubsidyNoticeOut,
    UserOut,
)

router = APIRouter(tags=["用户认证"])


@router.post(
    "/api/auth/login",
    response_model=ApiResponse[LoginOut],
    summary="统一登录（含角色校验）",
    description="学生/商家/超管统一入口。商家未通过审核返回 20003。",
)
def login(request: LoginRequest, db: Session = Depends(get_db)) -> ApiResponse[LoginOut]:
    return ApiResponse(data=service.login(db, request))


@router.post(
    "/api/auth/register",
    response_model=ApiResponse[RegisterOut],
    summary="学生/商家注册（区分角色）",
    description="学生学号即登录账号；商家注册后进入待审核状态。",
)
def register(
    request: RegisterRequest, db: Session = Depends(get_db)
) -> ApiResponse[RegisterOut]:
    return ApiResponse(data=service.register(db, request))


@router.post(
    "/api/auth/reset-password",
    response_model=ApiResponse[MessageOut],
    summary="重置密码为 123456",
)
def reset_password(
    request: ResetPasswordRequest, db: Session = Depends(get_db)
) -> ApiResponse[MessageOut]:
    service.reset_password(db, request)
    return ApiResponse(data=MessageOut(message="密码已重置为123456"))


@router.get(
    "/api/user/profile",
    response_model=ApiResponse[UserOut],
    response_model_exclude_none=True,
    summary="获取个人资料",
)
def get_profile(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UserOut]:
    return ApiResponse(data=service.get_profile(db, current_user))


@router.put(
    "/api/user/profile",
    response_model=ApiResponse[UserOut],
    response_model_exclude_none=True,
    summary="修改个人资料（偏好/禁忌/生活费等）",
)
def update_profile(
    request: ProfileUpdateRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[UserOut]:
    return ApiResponse(data=service.update_profile(db, current_user, request))


@router.get(
    "/api/user/subsidy/notices",
    response_model=ApiResponse[List[SubsidyNoticeOut]],
    summary="我的优惠发放通知（未读在前，已读保留为历史）",
)
def my_subsidy_notices(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[SubsidyNoticeOut]]:
    from app.admin import service as admin_service

    return ApiResponse(data=admin_service.list_my_notices(db, current_user.id))


@router.put(
    "/api/user/subsidy/notices/{grant_id}/read",
    response_model=ApiResponse[MessageOut],
    summary="标记优惠通知已读",
)
def read_subsidy_notice(
    grant_id: int,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MessageOut]:
    from app.admin import service as admin_service

    admin_service.mark_notice_read(db, current_user.id, grant_id)
    return ApiResponse(data=MessageOut(message="ok"))


@router.post(
    "/api/user/behavior",
    response_model=ApiResponse[MessageOut],
    summary="记录用户行为",
    description="behavior_type：1 浏览，2 收藏，3 下单，4 分享。",
)
def record_behavior(
    request: BehaviorRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MessageOut]:
    service.record_behavior(db, current_user, request.product_id, request.behavior_type)
    return ApiResponse(data=MessageOut(message="ok"))
