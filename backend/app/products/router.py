"""商品模块路由（何睿涵负责）。

发布/下架需商家登录且审核通过；推荐/猜你喜欢/收藏需登录；
列表与详情为公开接口（详情携带 Token 时自动记录浏览行为并返回收藏状态）。
"""
from __future__ import annotations

from typing import List, Optional

import jwt
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.auth import CurrentUser, bearer_scheme, get_current_user
from app.config import settings
from app.database import get_db
from app.errors import BusinessError
from app.models import User
from app.products import service
from app.schemas import (
    ApiResponse,
    FavoriteOut,
    FavoriteRequest,
    ProductCreateRequest,
    ProductOut,
    ProductPageOut,
)

router = APIRouter(tags=["商品"])


def get_optional_user(
    credentials=Depends(bearer_scheme),
    db: Session = Depends(get_db),
) -> Optional[User]:
    """可选登录：有有效 Token 返回 User，否则返回 None（不抛错）。"""
    if credentials is None or credentials.scheme.lower() != "bearer":
        return None
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"require": ["exp"], "verify_sub": False},
        )
        user_id = int(payload.get("sub", payload.get("user_id")))
    except (jwt.PyJWTError, TypeError, ValueError):
        return None
    user = db.get(User, user_id)
    if user is None or user.status != 1:
        return None
    return user


def _require_role(current: CurrentUser, role: int) -> None:
    if current.role != role:
        raise BusinessError(403, "当前角色无权访问该接口", 403)


@router.post(
    "/api/products",
    response_model=ApiResponse[ProductOut],
    summary="商家发布商品（自动触发 AI 风控）",
    description="风控命中拦截规则时返回 41001/41002/41003，并写入风控日志。",
)
def create_product(
    request: ProductCreateRequest,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProductOut]:
    _require_role(current, 2)
    merchant = service.get_merchant_or_403(db, current.id)
    return ApiResponse(data=service.create_product(db, merchant, request))


@router.get(
    "/api/products",
    response_model=ApiResponse[ProductPageOut],
    summary="商品列表（分页/筛选/排序）",
)
def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=50),
    category: Optional[str] = None,
    keyword: Optional[str] = None,
    sort: str = Query("newest", description="newest/price_asc/price_desc/expire"),
    db: Session = Depends(get_db),
) -> ApiResponse[ProductPageOut]:
    return ApiResponse(data=service.list_products(db, page, size, category, keyword, sort))


@router.get(
    "/api/products/recommend",
    response_model=ApiResponse[List[ProductOut]],
    summary="AI 个性化推荐首页",
)
def get_recommend(
    lat: Optional[float] = Query(None, description="用户纬度（可选，用于距离排序）"),
    lng: Optional[float] = Query(None, description="用户经度（可选）"),
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProductOut]]:
    return ApiResponse(data=service.get_recommendations(db, current.id, lat, lng))


@router.get(
    "/api/products/guess-you-like",
    response_model=ApiResponse[List[ProductOut]],
    summary="猜你喜欢（协同过滤）",
)
def get_guess(
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProductOut]]:
    return ApiResponse(data=service.get_guess_you_like(db, current.id))


@router.get(
    "/api/products/{product_id}",
    response_model=ApiResponse[ProductOut],
    response_model_exclude_none=True,
    summary="商品详情（自动记录浏览）",
)
def get_detail(
    product_id: int,
    user: Optional[User] = Depends(get_optional_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProductOut]:
    return ApiResponse(data=service.get_product_detail(db, product_id, user))


@router.post(
    "/api/products/{product_id}/favorite",
    response_model=ApiResponse[FavoriteOut],
    summary="收藏 / 取消收藏",
)
def favorite(
    product_id: int,
    request: FavoriteRequest,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[FavoriteOut]:
    result = service.toggle_favorite(db, current.id, product_id, request.favorite)
    return ApiResponse(data=FavoriteOut(**result))


@router.put(
    "/api/products/{product_id}/offline",
    response_model=ApiResponse[ProductOut],
    summary="商家下架商品",
)
def offline(
    product_id: int,
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[ProductOut]:
    _require_role(current, 2)
    merchant = service.get_merchant_or_403(db, current.id)
    return ApiResponse(data=service.offline_product(db, merchant, product_id))


@router.get(
    "/api/user/favorites",
    response_model=ApiResponse[List[ProductOut]],
    summary="我的收藏列表（个人中心）",
)
def my_favorites(
    current: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[ProductOut]]:
    return ApiResponse(data=service.list_my_favorites(db, current.id))
