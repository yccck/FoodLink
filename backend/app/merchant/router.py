"""商家端个人中心路由（何睿涵负责）。

仅商家（role=2）可访问，用于查看 / 提交店铺资料修改。
"""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.errors import BusinessError
from app.merchant import service
from app.schemas import ApiResponse, MerchantProfileOut, MerchantProfileUpdateRequest

router = APIRouter(tags=["商家"])


def _require_merchant(current: CurrentUser) -> int:
    if current.role != 2:
        raise BusinessError(403, "仅商家可访问", 403)
    return current.id


@router.get(
    "/api/merchant/profile",
    response_model=ApiResponse[MerchantProfileOut],
    summary="商家店铺资料（含待审核资料）",
)
def get_profile(
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MerchantProfileOut]:
    user_id = _require_merchant(current)
    return ApiResponse(data=service.get_profile(db, user_id))


@router.put(
    "/api/merchant/profile",
    response_model=ApiResponse[MerchantProfileOut],
    summary="商家提交资料修改（等待超管审核）",
)
def update_profile(
    request: MerchantProfileUpdateRequest,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[MerchantProfileOut]:
    user_id = _require_merchant(current)
    return ApiResponse(data=service.update_profile(db, user_id, request))
