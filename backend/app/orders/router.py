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
    WalletActionOut,
    WalletActionRequest,
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
    summary="查询订单钱包概览",
    description="学生查看余额、托管与月消费；商家查看钱包、待结算与月销售。",
)
def get_order_summary(
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[OrderSummaryOut]:
    return ApiResponse(data=service.get_order_summary(db, current_user))


@router.post(
    "/wallet/recharge",
    response_model=ApiResponse[WalletActionOut],
    summary="钱包演示充值",
    description="学生或商家向演示钱包充值，不连接真实支付渠道。",
)
def recharge_wallet(
    request: WalletActionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletActionOut]:
    return ApiResponse(
        data=service.change_wallet_balance(db, current_user, request, "recharge")
    )


@router.post(
    "/wallet/withdraw",
    response_model=ApiResponse[WalletActionOut],
    summary="钱包演示提现",
    description="学生或商家从可用余额中演示提现，平台托管金额不可提现。",
)
def withdraw_wallet(
    request: WalletActionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> ApiResponse[WalletActionOut]:
    return ApiResponse(
        data=service.change_wallet_balance(db, current_user, request, "withdraw")
    )


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
