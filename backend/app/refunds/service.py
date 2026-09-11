from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import ADMIN_ROLE, STUDENT_ROLE, CurrentUser
from app.business_hours import calculate_pickup_deadline
from app.errors import BusinessError
from app.models import (
    Merchant,
    Order,
    Product,
    RefundApplication,
    User,
    WalletAccount,
)
from app.refunds.schemas import (
    CreateRefundApplicationRequest,
    RefundApplicationOut,
)
from app.timeutils import format_datetime, now_shanghai_naive


ORDER_COMPLETED = 1
ORDER_CLOSED = 2
APPLICATION_PENDING = 0
APPLICATION_APPROVED = 1
APPLICATION_REJECTED = 2
CENT = Decimal("0.01")
PLATFORM_FEE_RATE = Decimal("0.001")


def _application_query():
    return (
        select(RefundApplication, Order, Product, Merchant, User)
        .join(Order, Order.id == RefundApplication.order_id)
        .join(Product, Product.id == Order.product_id)
        .join(Merchant, Merchant.id == Product.merchant_id)
        .join(User, User.id == RefundApplication.user_id)
    )


def _order_query():
    return (
        select(Order, Product, Merchant)
        .join(Product, Product.id == Order.product_id)
        .join(Merchant, Merchant.id == Product.merchant_id)
    )


def _total_amount(order: Order) -> Decimal:
    return (Decimal(order.price) * order.quantity).quantize(
        CENT, rounding=ROUND_HALF_UP
    )


def _merchant_receivable(order: Order) -> Decimal:
    total = _total_amount(order)
    fee = (total * PLATFORM_FEE_RATE).quantize(CENT, rounding=ROUND_HALF_UP)
    return (total - fee).quantize(CENT, rounding=ROUND_HALF_UP)


def _to_out(row) -> RefundApplicationOut:
    application, order, product, merchant, student = row
    return RefundApplicationOut(
        id=application.id,
        order_id=order.id,
        product_title=product.title,
        product_image=product.image or "",
        shop_name=merchant.shop_name,
        student_name=student.name,
        student_id=student.student_id or "",
        total_amount=_total_amount(order),
        reason=application.reason,
        evidence_image=application.evidence_image or "",
        status=application.status,
        admin_remark=application.admin_remark or "",
        created_at=format_datetime(application.created_at),
        reviewed_at=format_datetime(application.reviewed_at),
    )


def _is_merchant_confirmed(order: Order, product: Product) -> bool:
    if order.status != ORDER_COMPLETED or order.picked_at is None:
        return False
    pickup_deadline = calculate_pickup_deadline(
        order.created_at,
        product.expire_time,
        product.business_close_time,
    )
    return order.picked_at != pickup_deadline


def create_refund_application(
    db: Session,
    current_user: CurrentUser,
    order_id: int,
    request: CreateRefundApplicationRequest,
) -> RefundApplicationOut:
    if current_user.role != STUDENT_ROLE:
        raise BusinessError(403, "仅下单学生可以提交食品问题售后", 403)

    row = db.execute(_order_query().where(Order.id == order_id)).one_or_none()
    if row is None:
        raise BusinessError(404, "订单不存在", 404)
    order, product, _merchant = row
    if order.user_id != current_user.id:
        raise BusinessError(403, "无权为该订单提交售后", 403)
    if not _is_merchant_confirmed(order, product):
        if order.status == ORDER_COMPLETED:
            raise BusinessError(400, "未按时领取而自动完成的订单不支持退款", 400)
        raise BusinessError(400, "只有实际领取后发现食品问题才能提交管理员审核", 400)
    existing = db.scalar(
        select(RefundApplication.id).where(RefundApplication.order_id == order.id)
    )
    if existing is not None:
        raise BusinessError(400, "该订单已经提交过售后申请", 400)

    reason = request.reason.strip()
    if len(reason) < 5:
        raise BusinessError(400, "请至少填写 5 个字的问题说明", 400)
    application = RefundApplication(
        order_id=order.id,
        user_id=current_user.id,
        reason=reason,
        evidence_image=request.evidence_image or None,
        status=APPLICATION_PENDING,
    )
    db.add(application)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise BusinessError(400, "该订单已经提交过售后申请", 400)

    result = db.execute(
        _application_query().where(RefundApplication.id == application.id)
    ).one()
    return _to_out(result)


def list_student_refund_applications(
    db: Session, current_user: CurrentUser
) -> List[RefundApplicationOut]:
    if current_user.role != STUDENT_ROLE:
        raise BusinessError(403, "仅学生可以查看本人售后申请", 403)
    rows = db.execute(
        _application_query()
        .where(RefundApplication.user_id == current_user.id)
        .order_by(RefundApplication.created_at.desc())
    ).all()
    return [_to_out(row) for row in rows]


def list_admin_refund_applications(
    db: Session,
    current_user: CurrentUser,
    status: Optional[int],
) -> List[RefundApplicationOut]:
    if current_user.role != ADMIN_ROLE:
        raise BusinessError(403, "仅超管可以审核退款申请", 403)
    if status is not None and status not in (
        APPLICATION_PENDING,
        APPLICATION_APPROVED,
        APPLICATION_REJECTED,
    ):
        raise BusinessError(400, "审核状态仅支持 0、1、2", 400)
    statement = _application_query()
    if status is not None:
        statement = statement.where(RefundApplication.status == status)
    rows = db.execute(
        statement.order_by(RefundApplication.created_at.desc())
    ).all()
    return [_to_out(row) for row in rows]


def audit_refund_application(
    db: Session,
    current_user: CurrentUser,
    application_id: int,
    audit_status: int,
    admin_remark: str,
) -> RefundApplicationOut:
    if current_user.role != ADMIN_ROLE:
        raise BusinessError(403, "仅超管可以审核退款申请", 403)
    if audit_status not in (APPLICATION_APPROVED, APPLICATION_REJECTED):
        raise BusinessError(400, "audit_status 仅支持 1（通过）或 2（驳回）", 400)
    remark = admin_remark.strip()
    if audit_status == APPLICATION_REJECTED and not remark:
        raise BusinessError(400, "驳回申请时请填写审核说明", 400)

    row = db.execute(
        _application_query().where(RefundApplication.id == application_id)
    ).one_or_none()
    if row is None:
        raise BusinessError(404, "退款申请不存在", 404)
    application, order, product, merchant, _student = row
    if application.status != APPLICATION_PENDING:
        raise BusinessError(400, "该退款申请已经审核，请勿重复操作", 400)

    reviewed_at = now_shanghai_naive()
    claimed = db.execute(
        update(RefundApplication)
        .where(
            RefundApplication.id == application.id,
            RefundApplication.status == APPLICATION_PENDING,
        )
        .values(
            status=audit_status,
            admin_remark=remark or (
                "食品质量问题审核通过，款项原路退回"
                if audit_status == APPLICATION_APPROVED
                else ""
            ),
            reviewer_id=current_user.id,
            reviewed_at=reviewed_at,
        )
        .execution_options(synchronize_session=False)
    )
    if claimed.rowcount != 1:
        db.rollback()
        raise BusinessError(400, "该退款申请已经审核，请勿重复操作", 400)

    if audit_status == APPLICATION_APPROVED:
        if not _is_merchant_confirmed(order, product):
            raise BusinessError(400, "订单状态已变化，当前无法执行退款", 400)
        wallet = db.get(WalletAccount, merchant.user_id)
        receivable = _merchant_receivable(order)
        if wallet is None or Decimal(wallet.balance) < receivable:
            raise BusinessError(400, "商家结算记录余额不足，暂时无法退款", 400)
        wallet.balance = (Decimal(wallet.balance) - receivable).quantize(CENT)
        wallet.updated_at = reviewed_at
        order.status = ORDER_CLOSED
        order.close_reason = "admin_refund"
        order.closed_at = reviewed_at
    db.commit()
    db.expire_all()

    result = db.execute(
        _application_query().where(RefundApplication.id == application.id)
    ).one()
    return _to_out(result)
