from __future__ import annotations

import secrets
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional

from sqlalchemy import case, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import ADMIN_ROLE, MERCHANT_ROLE, STUDENT_ROLE, CurrentUser
from app.business_hours import calculate_pickup_deadline
from app.errors import BusinessError
from app.models import Behavior, Merchant, Order, Product, User, WalletAccount
from app.schemas import (
    CreateOrderRequest,
    OrderOut,
    OrderSummaryOut,
    WalletActionOut,
    WalletActionRequest,
)
from app.timeutils import format_datetime, now_shanghai_naive

ORDER_PENDING = 0
ORDER_PICKED_UP = 1
ORDER_EXPIRED = 2
PRODUCT_OFFLINE = 0
PRODUCT_ON_SALE = 1
PRODUCT_SOLD_OUT = 2
MERCHANT_APPROVED = 1
ORDER_BEHAVIOR = 3
MAX_PICKUP_CODE_ATTEMPTS = 20
MAX_CREATE_ATTEMPTS = 3
PLATFORM_FEE_RATE = Decimal("0.001")
PLATFORM_FEE_RATE_DISPLAY = "0.1%"
CENT = Decimal("0.01")


def _order_query():
    return (
        select(Order, Product, Merchant, User)
        .join(Product, Product.id == Order.product_id)
        .join(Merchant, Merchant.id == Product.merchant_id)
        .join(User, User.id == Order.user_id)
    )


def _money_breakdown(order: Order):
    total_amount = (Decimal(order.price) * order.quantity).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    platform_fee = (total_amount * PLATFORM_FEE_RATE).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    merchant_receivable = (total_amount - platform_fee).quantize(
        CENT, rounding=ROUND_HALF_UP
    )
    return total_amount, platform_fee, merchant_receivable


def _to_order_out(row, include_student: bool) -> OrderOut:
    order, product, merchant, student = row
    now = now_shanghai_naive()
    pickup_deadline = calculate_pickup_deadline(
        order.created_at,
        product.expire_time,
        product.business_close_time,
    )
    total_amount, platform_fee, merchant_receivable = _money_breakdown(order)
    if order.status == ORDER_EXPIRED:
        platform_fee = Decimal("0.00")
        merchant_receivable = Decimal("0.00")
        payment_status = "refunded"
    else:
        payment_status = (
            "settled" if order.status == ORDER_PICKED_UP else "escrowed"
        )

    completion_type = None
    if order.status == ORDER_PICKED_UP and order.picked_at is not None:
        completion_type = (
            "auto_timeout"
            if order.picked_at == pickup_deadline
            else "merchant_confirmed"
        )

    return OrderOut(
        id=order.id,
        product_id=product.id,
        product_title=product.title,
        product_image=product.image or "",
        shop_name=merchant.shop_name,
        original_price=order.original_price,
        price=order.price,
        total_amount=total_amount,
        quantity=order.quantity,
        status=order.status,
        pickup_code=order.pickup_code,
        expire_time=format_datetime(product.expire_time),
        business_open_time=product.business_open_time,
        business_close_time=product.business_close_time,
        pickup_deadline=format_datetime(pickup_deadline),
        remaining_seconds=(
            max(0, int((pickup_deadline - now).total_seconds()))
            if order.status == ORDER_PENDING
            else 0
        ),
        location=product.location,
        created_at=format_datetime(order.created_at),
        picked_at=format_datetime(order.picked_at),
        payment_status=payment_status,
        platform_fee_rate=PLATFORM_FEE_RATE_DISPLAY,
        platform_fee=platform_fee,
        merchant_receivable=merchant_receivable,
        settled_at=(
            format_datetime(order.picked_at)
            if payment_status == "settled"
            else None
        ),
        completion_type=completion_type,
        student_name=student.name if include_student else None,
        student_id=student.student_id if include_student else None,
        phone=student.phone if include_student else None,
    )


def _merchant_for_user(db: Session, user_id: int) -> Merchant:
    merchant = db.scalar(select(Merchant).where(Merchant.user_id == user_id))
    if merchant is None or merchant.audit_status != MERCHANT_APPROVED:
        raise BusinessError(403, "商家账号未通过审核或无商家资料", 403)
    return merchant


def _wallet_balance(db: Session, user_id: int) -> Decimal:
    wallet = db.get(WalletAccount, user_id)
    return Decimal(wallet.balance) if wallet is not None else Decimal("0.00")


def _credit_wallet(
    db: Session, user_id: int, amount: Decimal, settled_at
) -> None:
    result = db.execute(
        update(WalletAccount)
        .where(WalletAccount.user_id == user_id)
        .values(
            balance=WalletAccount.balance + amount,
            updated_at=settled_at,
        )
        .execution_options(synchronize_session=False)
    )
    if result.rowcount == 0:
        db.add(
            WalletAccount(
                user_id=user_id,
                balance=amount,
                updated_at=settled_at,
            )
        )


def _credit_order_merchant(
    db: Session, merchant_user_id: int, order: Order, settled_at
) -> None:
    _total, _fee, merchant_receivable = _money_breakdown(order)
    _credit_wallet(db, merchant_user_id, merchant_receivable, settled_at)


def auto_complete_overdue_orders(db: Session) -> int:
    """Complete orders at shop closing time and release demo escrow settlement."""

    now = now_shanghai_naive()
    overdue_orders = db.execute(
        select(Order, Product, Merchant.user_id)
        .join(Product, Product.id == Order.product_id)
        .join(Merchant, Merchant.id == Product.merchant_id)
        .where(Order.status == ORDER_PENDING)
    ).all()
    completed = 0
    for order, product, merchant_user_id in overdue_orders:
        settled_at = calculate_pickup_deadline(
            order.created_at,
            product.expire_time,
            product.business_close_time,
        )
        if settled_at > now:
            continue
        result = db.execute(
            update(Order)
            .where(Order.id == order.id, Order.status == ORDER_PENDING)
            .values(
                status=ORDER_PICKED_UP,
                picked_at=settled_at,
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount == 1:
            _credit_order_merchant(db, merchant_user_id, order, settled_at)
            completed += 1
    if completed:
        db.commit()
    return completed


def _generate_pickup_code(db: Session) -> str:
    for _ in range(MAX_PICKUP_CODE_ATTEMPTS):
        code = str(secrets.randbelow(900000) + 100000)
        exists = db.scalar(select(Order.id).where(Order.pickup_code == code))
        if exists is None:
            return code
    raise BusinessError(50000, "取货码生成失败，请稍后重试", 500)


def _load_order(db: Session, order_id: int):
    return db.execute(_order_query().where(Order.id == order_id)).one_or_none()


def _raise_product_unavailable(db: Session, product_id: int, quantity: int) -> None:
    product = db.get(Product, product_id)
    if product is None:
        raise BusinessError(404, "商品不存在", 404)
    if product.status != PRODUCT_ON_SALE:
        raise BusinessError(400, "商品已售罄或已下架", 400)
    if product.expire_time <= now_shanghai_naive():
        raise BusinessError(400, "商品已过期，无法下单", 400)
    if product.quantity < quantity:
        raise BusinessError(400, "商品库存不足", 400)
    raise BusinessError(400, "商品暂时无法下单，请刷新后重试", 400)


def create_order(
    db: Session, current_user: CurrentUser, request: CreateOrderRequest
) -> OrderOut:
    if current_user.role != STUDENT_ROLE:
        raise BusinessError(403, "仅学生可以下单", 403)

    for attempt in range(MAX_CREATE_ATTEMPTS):
        product = db.get(Product, request.product_id)
        if product is None:
            raise BusinessError(404, "商品不存在", 404)
        now = now_shanghai_naive()
        if product.status != PRODUCT_ON_SALE:
            raise BusinessError(400, "商品已售罄或已下架", 400)
        if product.expire_time <= now:
            raise BusinessError(400, "商品已过期，无法下单", 400)
        if product.quantity < request.quantity:
            raise BusinessError(400, "商品库存不足", 400)

        pickup_code = _generate_pickup_code(db)
        decrement = db.execute(
            update(Product)
            .where(
                Product.id == product.id,
                Product.status == PRODUCT_ON_SALE,
                Product.expire_time > now,
                Product.quantity >= request.quantity,
            )
            .values(
                quantity=Product.quantity - request.quantity,
                status=case(
                    (Product.quantity == request.quantity, PRODUCT_SOLD_OUT),
                    else_=Product.status,
                ),
                order_count=Product.order_count + 1,
            )
            .execution_options(synchronize_session=False)
        )
        if decrement.rowcount != 1:
            db.rollback()
            _raise_product_unavailable(db, request.product_id, request.quantity)

        order = Order(
            user_id=current_user.id,
            product_id=product.id,
            quantity=request.quantity,
            original_price=Decimal(product.original_price),
            price=Decimal(product.discount_price),
            pickup_code=pickup_code,
            status=ORDER_PENDING,
            created_at=now,
        )
        db.add(order)
        db.add(
            Behavior(
                user_id=current_user.id,
                product_id=product.id,
                behavior_type=ORDER_BEHAVIOR,
                created_at=now,
            )
        )

        try:
            db.commit()
        except IntegrityError as exc:
            db.rollback()
            if "pickup_code" in str(exc) and attempt + 1 < MAX_CREATE_ATTEMPTS:
                continue
            raise BusinessError(50000, "订单创建失败，请稍后重试", 500)

        row = _load_order(db, order.id)
        if row is None:
            raise BusinessError(50000, "订单创建失败，请稍后重试", 500)
        return _to_order_out(row, include_student=False)

    raise BusinessError(50000, "取货码生成失败，请稍后重试", 500)


def list_orders(
    db: Session, current_user: CurrentUser, status: Optional[int]
) -> List[OrderOut]:
    if current_user.role not in (STUDENT_ROLE, MERCHANT_ROLE):
        raise BusinessError(403, "仅学生或商家可以查看订单", 403)

    merchant = None
    if current_user.role == MERCHANT_ROLE:
        merchant = _merchant_for_user(db, current_user.id)

    auto_complete_overdue_orders(db)
    statement = _order_query()
    include_student = current_user.role == MERCHANT_ROLE
    if include_student:
        statement = statement.where(Product.merchant_id == merchant.id)
    else:
        statement = statement.where(Order.user_id == current_user.id)
    if status is not None:
        statement = statement.where(Order.status == status)
    rows = db.execute(statement.order_by(Order.created_at.desc(), Order.id.desc())).all()
    return [_to_order_out(row, include_student=include_student) for row in rows]


def _month_bounds(now):
    start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    if start.month == 12:
        end = start.replace(year=start.year + 1, month=1)
    else:
        end = start.replace(month=start.month + 1)
    return start, end


def get_order_summary(
    db: Session, current_user: CurrentUser
) -> OrderSummaryOut:
    if current_user.role not in (STUDENT_ROLE, MERCHANT_ROLE):
        raise BusinessError(403, "仅学生或商家可以查看钱包概览", 403)

    merchant = None
    statement = _order_query()
    if current_user.role == MERCHANT_ROLE:
        merchant = _merchant_for_user(db, current_user.id)
        statement = statement.where(Product.merchant_id == merchant.id)
    else:
        statement = statement.where(Order.user_id == current_user.id)

    auto_complete_overdue_orders(db)
    rows = db.execute(statement).all()
    start, end = _month_bounds(now_shanghai_naive())
    monthly_rows = [
        row
        for row in rows
        if start <= row[0].created_at < end and row[0].status != ORDER_EXPIRED
    ]
    pending_rows = [row for row in rows if row[0].status == ORDER_PENDING]
    completed_rows = [row for row in monthly_rows if row[0].status == ORDER_PICKED_UP]

    escrow_amount = sum(
        (_money_breakdown(row[0])[0] for row in pending_rows),
        Decimal("0.00"),
    )
    monthly_total = sum(
        (_money_breakdown(row[0])[0] for row in monthly_rows),
        Decimal("0.00"),
    )
    monthly_fee = sum(
        (_money_breakdown(row[0])[1] for row in completed_rows),
        Decimal("0.00"),
    )
    monthly_income = sum(
        (_money_breakdown(row[0])[2] for row in completed_rows),
        Decimal("0.00"),
    )
    monthly_item_count = sum(row[0].quantity for row in monthly_rows)

    is_merchant = current_user.role == MERCHANT_ROLE
    return OrderSummaryOut(
        role=current_user.role,
        available_balance=_wallet_balance(db, current_user.id),
        escrow_amount=escrow_amount,
        monthly_sales=monthly_total if is_merchant else Decimal("0.00"),
        monthly_spending=monthly_total if not is_merchant else Decimal("0.00"),
        monthly_income=monthly_income if is_merchant else Decimal("0.00"),
        monthly_platform_fee=monthly_fee if is_merchant else Decimal("0.00"),
        monthly_order_count=len(monthly_rows),
        monthly_item_count=monthly_item_count,
        monthly_completed_count=len(completed_rows),
    )


def change_wallet_balance(
    db: Session,
    current_user: CurrentUser,
    request: WalletActionRequest,
    action: str,
) -> WalletActionOut:
    if current_user.role not in (STUDENT_ROLE, MERCHANT_ROLE):
        raise BusinessError(403, "仅学生或商家可以操作钱包", 403)
    if action not in ("recharge", "withdraw"):
        raise BusinessError(400, "不支持的钱包操作", 400)

    amount = Decimal(request.amount).quantize(CENT, rounding=ROUND_HALF_UP)
    processed_at = now_shanghai_naive()
    if action == "recharge":
        _credit_wallet(db, current_user.id, amount, processed_at)
    else:
        result = db.execute(
            update(WalletAccount)
            .where(
                WalletAccount.user_id == current_user.id,
                WalletAccount.balance >= amount,
            )
            .values(
                balance=WalletAccount.balance - amount,
                updated_at=processed_at,
            )
            .execution_options(synchronize_session=False)
        )
        if result.rowcount != 1:
            db.rollback()
            raise BusinessError(400, "可用余额不足，无法提现", 400)

    db.commit()
    db.expire_all()
    return WalletActionOut(
        action=action,
        amount=amount,
        available_balance=_wallet_balance(db, current_user.id),
        processed_at=format_datetime(processed_at),
    )


def _pickup_loaded_order(
    db: Session,
    current_user: CurrentUser,
    row,
    merchant: Optional[Merchant],
) -> OrderOut:
    order, product, _shop, _student = row
    if merchant is not None and product.merchant_id != merchant.id:
        raise BusinessError(403, "无权核销该订单", 403)
    if order.status == ORDER_PICKED_UP:
        raise BusinessError(400, "订单已核销，请勿重复操作", 400)
    if order.status == ORDER_EXPIRED:
        raise BusinessError(400, "订单已过期，无法核销", 400)

    picked_at = now_shanghai_naive()
    result = db.execute(
        update(Order)
        .where(Order.id == order.id, Order.status == ORDER_PENDING)
        .values(status=ORDER_PICKED_UP, picked_at=picked_at)
        .execution_options(synchronize_session=False)
    )
    if result.rowcount != 1:
        db.rollback()
        latest = _load_order(db, order.id)
        if latest is not None and latest[0].status == ORDER_PICKED_UP:
            raise BusinessError(400, "订单已核销，请勿重复操作", 400)
        raise BusinessError(400, "订单状态已变化，请刷新后重试", 400)

    _credit_order_merchant(db, _shop.user_id, order, picked_at)
    db.commit()
    db.expire_all()
    updated = _load_order(db, order.id)
    if updated is None:
        raise BusinessError(404, "订单不存在", 404)
    return _to_order_out(updated, include_student=True)


def pickup_order(
    db: Session, current_user: CurrentUser, order_id: int
) -> OrderOut:
    if current_user.role not in (MERCHANT_ROLE, ADMIN_ROLE):
        raise BusinessError(403, "仅商家或管理员可以核销订单", 403)
    merchant = (
        _merchant_for_user(db, current_user.id)
        if current_user.role == MERCHANT_ROLE
        else None
    )
    auto_complete_overdue_orders(db)
    row = _load_order(db, order_id)
    if row is None:
        raise BusinessError(404, "订单不存在", 404)
    return _pickup_loaded_order(db, current_user, row, merchant)


def verify_pickup_code(
    db: Session, current_user: CurrentUser, pickup_code: str
) -> OrderOut:
    if current_user.role not in (MERCHANT_ROLE, ADMIN_ROLE):
        raise BusinessError(403, "仅商家或管理员可以核销订单", 403)
    merchant = (
        _merchant_for_user(db, current_user.id)
        if current_user.role == MERCHANT_ROLE
        else None
    )
    auto_complete_overdue_orders(db)
    row = db.execute(
        _order_query().where(Order.pickup_code == pickup_code)
    ).one_or_none()
    if row is None:
        raise BusinessError(400, "取货码无效", 400)
    return _pickup_loaded_order(db, current_user, row, merchant)
