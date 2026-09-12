"""超管后台业务逻辑（何睿涵负责）。

功能：商家审核、风控日志管理、用户禁用/启用、平台数据看板。
所有接口要求 role=3（超管），由路由层统一鉴权。
"""
from __future__ import annotations

from decimal import Decimal
from typing import List, Optional

from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.errors import BusinessError
from app.models import (
    Merchant,
    Order,
    Product,
    RiskLog,
    SubsidyGrant,
    User,
    WalletAccount,
)
from app.schemas import (
    AdminPendingOut,
    GrantSubsidyRequest,
    InjectPoolRequest,
    MerchantPendingOut,
    RiskLogOut,
    StatisticsOut,
    StudentConsumptionOut,
    SubsidyGrantOut,
    SubsidyNoticeOut,
    SubsidyPoolOut,
)
from app.timeutils import now_shanghai_naive

CENT = Decimal("0.01")
# 计入消费的订单状态：0 待领取、1 已完成；2 已关闭（退款/过期）不计入
CONSUMED_ORDER_STATUS = (0, 1)
# 优惠分配流水类型
GRANT_TYPE_STUDENT = 1
GRANT_TYPE_INJECT = 2
# 平台服务费率，与 orders/service.py 保持一致
PLATFORM_FEE_RATE = Decimal("0.001")


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


# ---------------------------------------------------------------- 优惠分配


def _platform_profit(db: Session) -> Decimal:
    """已结算订单的平台服务费累计（费率 0.1%）。"""

    total = db.scalar(
        select(func.coalesce(func.sum(Order.price * Order.quantity), 0)).where(
            Order.status.in_(CONSUMED_ORDER_STATUS)
        )
    )
    return (Decimal(total or 0) * PLATFORM_FEE_RATE).quantize(CENT)


def get_subsidy_pool(db: Session) -> SubsidyPoolOut:
    profit = _platform_profit(db)
    injected = db.scalar(
        select(func.coalesce(func.sum(SubsidyGrant.amount), 0)).where(
            SubsidyGrant.grant_type == GRANT_TYPE_INJECT
        )
    )
    granted = db.scalar(
        select(func.coalesce(func.sum(SubsidyGrant.amount), 0)).where(
            SubsidyGrant.grant_type == GRANT_TYPE_STUDENT
        )
    )
    injected = Decimal(injected or 0).quantize(CENT)
    granted = Decimal(granted or 0).quantize(CENT)
    return SubsidyPoolOut(
        platform_profit=profit,
        injected=injected,
        granted=granted,
        available=(profit + injected - granted).quantize(CENT),
    )


def grant_subsidy(
    db: Session,
    request: GrantSubsidyRequest,
    operator_id: int,
) -> List[SubsidyGrantOut]:
    """给指定学生发放优惠金额，自动划拨到学生钱包。"""

    user_ids = list(dict.fromkeys(request.user_ids or []))
    if not user_ids:
        raise BusinessError(400, "请选择要发放的学生", 400)

    amount = Decimal(request.amount or 0).quantize(CENT)
    if amount <= 0:
        raise BusinessError(400, "发放金额必须大于 0", 400)

    pool = get_subsidy_pool(db)
    need = (amount * len(user_ids)).quantize(CENT)
    if need > pool.available:
        raise BusinessError(
            400,
            f"可分配余额不足：剩余 {pool.available} 元，本次需要 {need} 元",
            400,
        )

    # 消费排名 -> 称号（前 3 名消费达人，其余为暖心帮扶对象）
    rank_map: dict[int, int] = {}
    for idx, row in enumerate(list_student_consumption(db, limit=500)):
        rank_map[row.user_id] = idx + 1

    created: List[SubsidyGrantOut] = []
    for uid in user_ids:
        user = db.get(User, uid)
        if user is None or user.role != 1:
            raise BusinessError(404, f"用户 {uid} 不存在或不是学生", 404)
        _credit_wallet(db, uid, amount)
        title = (request.title or "").strip() or _default_title(rank_map.get(uid))
        grant = SubsidyGrant(
            grant_type=GRANT_TYPE_STUDENT,
            user_id=uid,
            amount=amount,
            title=title,
            is_read=0,
            remark=request.remark or "优惠分配",
            operator_id=operator_id,
        )
        db.add(grant)
        created.append(grant)
    db.commit()
    for g in created:
        db.refresh(g)
    return [_to_grant_out(db, g) for g in created]


def inject_pool(
    db: Session, request: InjectPoolRequest, operator_id: int
) -> SubsidyPoolOut:
    """平台注入补贴资金（演示/运营补差用）。"""

    amount = Decimal(request.amount or 0).quantize(CENT)
    if amount <= 0:
        raise BusinessError(400, "注入金额必须大于 0", 400)
    db.add(
        SubsidyGrant(
            grant_type=GRANT_TYPE_INJECT,
            amount=amount,
            remark=request.remark or "平台注入",
            operator_id=operator_id,
        )
    )
    db.commit()
    return get_subsidy_pool(db)


def list_subsidy_grants(db: Session, limit: int = 100) -> List[SubsidyGrantOut]:
    if limit <= 0:
        limit = 100
    limit = min(limit, 500)
    rows = (
        db.execute(
            select(SubsidyGrant)
            .order_by(SubsidyGrant.id.desc())
            .limit(limit)
        )
        .scalars()
        .all()
    )
    return [_to_grant_out(db, g) for g in rows]


def _default_title(rank: Optional[int]) -> str:
    """按消费排名生成弹窗称号（避免直接出现困难/贫困等字眼）。"""

    if rank and rank <= 3:
        return "本月消费达人"
    return "本月暖心帮扶对象"


def list_my_notices(db: Session, user_id: int) -> List[SubsidyNoticeOut]:
    """学生端的优惠发放通知：未读在前，已读保留为历史记录。"""

    rows = (
        db.execute(
            select(SubsidyGrant)
            .where(
                SubsidyGrant.grant_type == GRANT_TYPE_STUDENT,
                SubsidyGrant.user_id == user_id,
            )
            .order_by(SubsidyGrant.is_read.asc(), SubsidyGrant.id.desc())
        )
        .scalars()
        .all()
    )
    return [
        SubsidyNoticeOut(
            id=g.id,
            title=g.title or "本月暖心帮扶对象",
            amount=g.amount,
            is_read=int(g.is_read or 0),
            created_at=g.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        )
        for g in rows
    ]


def mark_notice_read(db: Session, user_id: int, grant_id: int) -> None:
    grant = db.get(SubsidyGrant, grant_id)
    if grant is None or grant.user_id != user_id:
        raise BusinessError(404, "通知不存在", 404)
    grant.is_read = 1
    db.commit()


def _credit_wallet(db: Session, user_id: int, amount: Decimal) -> None:
    result = db.execute(
        update(WalletAccount)
        .where(WalletAccount.user_id == user_id)
        .values(balance=WalletAccount.balance + amount)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        db.add(WalletAccount(user_id=user_id, balance=amount))


def _to_grant_out(db: Session, g: SubsidyGrant) -> SubsidyGrantOut:
    user = db.get(User, g.user_id) if g.user_id else None
    operator = db.get(User, g.operator_id) if g.operator_id else None
    return SubsidyGrantOut(
        id=g.id,
        grant_type=g.grant_type,
        user_id=g.user_id,
        user_name=user.name if user else "",
        student_id=(user.student_id or "") if user else "",
        title=g.title or "",
        amount=g.amount,
        remark=g.remark or "",
        operator_name=operator.name if operator else "",
        created_at=g.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    )


# ------------------------------------------------------- 学生消费排行（优惠分配依据）


def list_student_consumption(
    db: Session, limit: int = 100
) -> List[StudentConsumptionOut]:
    """学生消费排行：先按消费次数降序，次数相同再按消费金额降序。"""

    if limit <= 0:
        limit = 100
    limit = min(limit, 500)

    order_count = func.count(Order.id)
    total_amount = func.coalesce(func.sum(Order.price * Order.quantity), 0)

    rows = db.execute(
        select(
            User.id,
            User.name,
            User.student_id,
            User.school,
            User.phone,
            order_count,
            total_amount,
            func.max(Order.created_at),
        )
        .join(Order, Order.user_id == User.id)
        .where(User.role == 1, Order.status.in_(CONSUMED_ORDER_STATUS))
        .group_by(User.id)
        .order_by(order_count.desc(), total_amount.desc())
        .limit(limit)
    ).all()

    result: List[StudentConsumptionOut] = []
    for uid, name, student_id, school, phone, count, amount, last_at in rows:
        result.append(
            StudentConsumptionOut(
                user_id=uid,
                name=name or "",
                student_id=student_id or "",
                school=school or "",
                phone=phone or "",
                order_count=int(count or 0),
                total_amount=Decimal(amount or 0).quantize(CENT),
                last_order_at=(
                    last_at.strftime("%Y-%m-%d %H:%M:%S") if last_at else None
                ),
            )
        )
    return result


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
