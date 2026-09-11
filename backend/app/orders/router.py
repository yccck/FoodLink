from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Path, Query
from sqlalchemy.orm import Session

from app.auth import CurrentUser, get_current_user
from app.database import get_db
from app.errors import BusinessError
from app.orders import service
from app.schemas import (
    ApiResponse,
    CreateOrderRequest,
    OrderOut,
    OrderSummaryOut,
    VerifyPickupCodeRequest,
)

router = APIRouter(prefix="/api/orders", tags=["订单管理"])


def _parse_status(raw_status: Optional[str]) -> Optional[int]:
    if raw_status is None or raw_status == "":
        return None
    if raw_status not in {"0", "1", "2"}:
        raise BusinessError(400, "订单状态仅支持 0、1、2", 400)
    return int(raw_status)


@router.post(
    "",
    response_model=ApiResponse[OrderOut],
    response_model_exclude_none=True,
    summary="学生下单",
    description="原子扣减库存并生成唯一的 6 位数字取货码。",
)
def create_order(
    request: CreateOrderRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrderOut]:
    return ApiResponse(data=service.create_order(db, current_user, request))


@router.get(
    "",
    response_model=ApiResponse[List[OrderOut]],
    response_model_exclude_none=True,
    summary="查询我的订单",
    description="学生只看到自己的订单；商家只看到本店商品产生的订单。",
)
def list_orders(
    status: Optional[str] = Query(
        default=None, description="0 待领取，1 已领取，2 已过期；空值表示全部"
    ),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[List[OrderOut]]:
    return ApiResponse(
        data=service.list_orders(db, current_user, _parse_status(status))
    )


@router.get(
    "/summary",
    response_model=ApiResponse[OrderSummaryOut],
    response_model_exclude_none=True,
    summary="查询本月订单概览",
    description="学生查看本月消费和订单数；商家查看本月销售、销量、服务费和净收入。",
)
def get_order_summary(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrderSummaryOut]:
    return ApiResponse(data=service.get_order_summary(db, current_user))


@router.put(
    "/{id}/refund",
    response_model=ApiResponse[OrderOut],
    response_model_exclude_none=True,
    summary="学生限时取消并退款",
    description="仅下单学生可在付款后 5 分钟内、且尚未核销时取消；库存恢复，款项原路退回。",
)
def refund_order(
    id: int = Path(gt=0, description="订单 ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrderOut]:
    return ApiResponse(data=service.refund_order(db, current_user, id))


@router.put(
    "/{id}/pickup",
    response_model=ApiResponse[OrderOut],
    response_model_exclude_none=True,
    summary="按订单 ID 核销",
)
def pickup_order(
    id: int = Path(gt=0, description="订单 ID"),
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrderOut]:
    return ApiResponse(data=service.pickup_order(db, current_user, id))


@router.post(
    "/verify",
    response_model=ApiResponse[OrderOut],
    response_model_exclude_none=True,
    summary="按取货码核销",
)
def verify_pickup_code(
    request: VerifyPickupCodeRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrderOut]:
    return ApiResponse(
        data=service.verify_pickup_code(db, current_user, request.pickup_code)
    )
