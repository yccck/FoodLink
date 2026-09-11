"""超管后台业务逻辑（何睿涵负责）。

功能：商家审核、风控日志管理、用户禁用/启用、平台数据看板。
所有接口要求 role=3（超管），由路由层统一鉴权。
"""
from __future__ import annotations

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.errors import BusinessError
from app.models import Merchant, Order, Product, RiskLog, User
from app.schemas import AdminPendingOut, MerchantPendingOut, RiskLogOut, StatisticsOut
from app.timeutils import now_shanghai_naive


# ---------------------------------------------------------------- 商家审核


def list_pending_merchants(db: Session) -> List[MerchantPendingOut]:
    rows = db.execute(
        select(Merchant, User)
        .join(User, User.id == Merchant.user_id)
        .where(Merchant.audit_status == 0)
        .order_by(Merchant.created_at.asc())
    ).all()
    return [
        MerchantPendingOut(
            id=m.id,
            user_id=m.user_id,
            shop_name=m.shop_name,
            license_img=m.license_img or "",
            location=m.location,
            login_name=u.login_name,
            phone=u.phone,
            created_at=m.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        for m, u in rows
    ]


def audit_merchant(db: Session, merchant_id: int, audit_status: int) -> None:
    if audit_status not in (1, 2):
        raise BusinessError(400, "audit_status 仅支持 1（通过）/ 2（驳回）", 400)
    merchant = db.get(Merchant, merchant_id)
    if merchant is None:
        raise BusinessError(404, "商家不存在", 404)
    if merchant.audit_status != 0:
        raise BusinessError(400, "该商家已审核，请勿重复操作", 400)
    merchant.audit_status = audit_status
    db.commit()


# ---------------------------------------------------------------- 管理员审核


def list_pending_admins(db: Session) -> List[AdminPendingOut]:
    """待审核的管理员注册申请（role=3 且 status=0）。"""
    rows = db.scalars(
        select(User)
        .where(User.role == 3, User.status == 0)
        .order_by(User.created_at.asc())
    ).all()
    return [
        AdminPendingOut(
            id=u.id,
            school=u.school or "",
            name=u.name or "",
            position=u.position or "",
            login_name=u.login_name,
            phone=u.phone,
            created_at=u.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        for u in rows
    ]


def audit_admin_user(db: Session, user_id: int, audit_status: int) -> None:
    """审核管理员：1 通过（恢复可登录）/ 2 驳回（禁用该账号）。"""
    if audit_status not in (1, 2):
        raise BusinessError(400, "audit_status 仅支持 1（通过）/ 2（驳回）", 400)
    user = db.get(User, user_id)
    if user is None or user.role != 3:
        raise BusinessError(404, "管理员不存在", 404)
    if user.status != 0:
        raise BusinessError(400, "该账号已审核，请勿重复操作", 400)
    if audit_status == 1:
        user.status = 1  # 审核通过，可登录
    else:
        db.delete(user)  # 驳回则删除注册申请
    db.commit()


# ---------------------------------------------------------------- 风控日志


def list_risk_logs(db: Session, is_resolved: Optional[int]) -> List[RiskLogOut]:
    conds = []
    if is_resolved is not None:
        conds.append(RiskLog.is_resolved == is_resolved)
    rows = db.execute(
        select(RiskLog, Product, Merchant)
        .join(Product, Product.id == RiskLog.product_id)
        .join(Merchant, Merchant.id == RiskLog.merchant_id)
        .where(*conds)
        .order_by(RiskLog.created_at.desc())
    ).all()
    return [
        RiskLogOut(
            id=log.id,
            product_id=log.product_id,
            product_title=p.title,
            merchant_id=log.merchant_id,
            shop_name=m.shop_name,
            risk_type=log.risk_type,
            risk_detail=log.risk_detail or "",
            is_resolved=log.is_resolved,
            created_at=log.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        for log, p, m in rows
    ]


def resolve_risk_log(db: Session, log_id: int) -> None:
    log = db.get(RiskLog, log_id)
    if log is None:
        raise BusinessError(404, "风控日志不存在", 404)
    log.is_resolved = 1
    db.flush()
    unresolved = db.scalar(
        select(func.count(RiskLog.id)).where(
            RiskLog.product_id == log.product_id,
            RiskLog.is_resolved == 0,
        )
    ) or 0
    product = db.get(Product, log.product_id)
    if product is not None and unresolved == 0:
        product.risk_flag = 0
        if product.status == 3:
            if product.expire_time <= now_shanghai_naive():
                product.status = 0
            else:
                product.status = 1 if product.quantity > 0 else 2
    db.commit()


# ---------------------------------------------------------------- 用户管理


def set_user_status(db: Session, user_id: int, status: int) -> None:
    if status not in (0, 1):
        raise BusinessError(400, "status 仅支持 0（禁用）/ 1（启用）", 400)
    user = db.get(User, user_id)
    if user is None:
        raise BusinessError(404, "用户不存在", 404)
    if user.role == 3:
        raise BusinessError(400, "不能禁用超管账号", 400)
    user.status = status
    db.commit()


# ---------------------------------------------------------------- 数据看板


def get_statistics(db: Session) -> StatisticsOut:
    def _count(column, *conds) -> int:
        return db.scalar(select(func.count(column)).where(*conds)) or 0

    return StatisticsOut(
        total_users=_count(User.id),
        total_students=_count(User.id, User.role == 1),
        total_merchants=_count(Merchant.id),
        pending_merchants=_count(Merchant.id, Merchant.audit_status == 0),
        total_products=_count(Product.id),
        on_sale_products=_count(Product.id, Product.status == 1),
        total_orders=_count(Order.id),
        risk_blocked_products=_count(Product.id, Product.risk_flag == 1),
        unresolved_risk_logs=_count(RiskLog.id, RiskLog.is_resolved == 0),
    )
